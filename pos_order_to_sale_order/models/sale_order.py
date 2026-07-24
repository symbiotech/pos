# Copyright (C) 2017 - Today: GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from psycopg2.errors import UniqueViolation

from odoo import Command, api, fields, models
from odoo.exceptions import AccessError, UserError

_POS_ACTION_CONFIG = {
    "draft": "iface_create_draft_sale_order",
    "confirmed": "iface_create_confirmed_sale_order",
    "delivered": "iface_create_delivered_sale_order",
    "invoiced": "iface_create_invoiced_sale_order",
}


class SaleOrder(models.Model):
    _inherit = "sale.order"

    pos_session_id = fields.Many2one(
        comodel_name="pos.session",
        string="PoS Session",
        readonly=True,
        index=True,
        copy=False,
    )
    pos_order_uuid = fields.Char(
        string="PoS Order UUID",
        readonly=True,
        index=True,
        copy=False,
        help="Technical link to the Point of Sale order that created this"
        " sale order. Used to avoid creating duplicates on retry.",
    )

    _pos_order_uuid_uniq = models.Constraint(
        "UNIQUE(pos_order_uuid)",
        "A sale order already exists for this Point of Sale order.",
    )

    @api.model
    def _get_create_line_vals_from_pos(self, order_data):
        """Return vals dicts for POS order lines marked as create commands only."""
        return [
            line_data[2]
            for line_data in order_data.get("lines") or []
            if (
                isinstance(line_data, (list, tuple))
                and len(line_data) >= 3
                and line_data[0] == Command.CREATE
                and isinstance(line_data[2], dict)
            )
        ]

    @api.model
    def _get_pos_session_for_order_creation(self, order_data):
        session = self.env["pos.session"].search(
            [("id", "=", order_data.get("session_id"))], limit=1
        )
        if not session:
            raise UserError(self.env._("No accessible POS session found."))
        if session.state not in ("opened", "opening_control"):
            raise UserError(
                self.env._(
                    "The POS session %(session)s is not open.",
                    session=session.display_name,
                )
            )
        return session

    @api.model
    def _check_pos_create_action_allowed(self, session, action):
        config_field = _POS_ACTION_CONFIG.get(action)
        if not config_field or not session.config_id[config_field]:
            raise UserError(
                self.env._(
                    "Creating a %(action)s sale order from this POS is not allowed.",
                    action=action,
                )
            )

    @api.model
    def _prepare_from_pos(self, order_data, line_vals_list, default_user=None):
        session = self.env["pos.session"].browse(order_data["session_id"])
        SaleOrderLine = self.env["sale.order.line"]
        order_lines = [
            Command.create(SaleOrderLine._prepare_from_pos(sequence, line_vals))
            for sequence, line_vals in enumerate(line_vals_list, start=1)
        ]
        user = default_user or self.env.user
        return {
            "partner_id": order_data["partner_id"],
            "pos_session_id": session.id,
            "pos_order_uuid": order_data.get("uuid") or False,
            "origin": self.env._("Point of Sale %s", session.name),
            "client_order_ref": order_data.get("name") or session.name,
            "user_id": order_data.get("user_id") or user.id,
            "pricelist_id": order_data.get("pricelist_id") or False,
            "fiscal_position_id": order_data.get("fiscal_position_id") or False,
            "order_line": order_lines,
        }

    @api.model
    def _find_sale_order_from_pos_uuid(self, pos_order_uuid):
        if not pos_order_uuid:
            return self.browse()
        return self.search([("pos_order_uuid", "=", pos_order_uuid)], limit=1)

    def _validate_pickings_from_pos(self):
        """Mark related pickings done, handling validate wizards when needed."""
        self.ensure_one()
        pickings = self.picking_ids.filtered(
            lambda p: p.state not in ("done", "cancel")
        )
        if not pickings:
            return
        for move in pickings.move_ids.filtered(lambda m: m.state != "cancel"):
            move.quantity = move.product_uom_qty
        pickings.move_ids.picked = True
        result = pickings.with_context(skip_backorder=True).button_validate()
        if isinstance(result, dict) and result.get("res_model"):
            wizard = (
                self.env[result["res_model"]]
                .with_context(**(result.get("context") or {}))
                .browse(result.get("res_id"))
            )
            if hasattr(wizard, "process_cancel_backorder"):
                wizard.process_cancel_backorder()
            elif hasattr(wizard, "process"):
                wizard.process()

    @api.model
    def create_order_from_pos(self, order_data, action):
        if not self.env.user.has_group("point_of_sale.group_pos_user"):
            raise AccessError(
                self.env._("Only Point of Sale users can create sale orders from PoS.")
            )
        if not order_data.get("partner_id"):
            raise UserError(
                self.env._("A customer is required to create a sale order.")
            )

        # Validate session/config with the caller's ACLs before elevating.
        session = self._get_pos_session_for_order_creation(order_data)
        self._check_pos_create_action_allowed(session, action)
        line_vals_list = self._get_create_line_vals_from_pos(order_data)
        if not line_vals_list:
            raise UserError(self.env._("No order lines to create a sale order from."))

        # POS cashiers may not have Sales ACLs.
        cashier = self.env.user
        self = self.sudo()

        # Idempotent: retries / double-Validate reuse the same sale order.
        existing = self._find_sale_order_from_pos_uuid(order_data.get("uuid"))
        if existing:
            return {"sale_order_id": existing.id}

        order_vals = self._prepare_from_pos(
            order_data, line_vals_list, default_user=cashier
        )
        try:
            with self.env.cr.savepoint():
                sale_order = self.with_context(
                    pos_order_lines_data=line_vals_list
                ).create(order_vals)
                sale_order._recompute_taxes()

                if action in ["confirmed", "delivered", "invoiced"]:
                    sale_order.action_confirm()

                if action in ["delivered", "invoiced"]:
                    sale_order._validate_pickings_from_pos()

                if action == "invoiced":
                    invoices = sale_order._create_invoices()
                    invoices.action_post()
        except UniqueViolation:
            existing = self._find_sale_order_from_pos_uuid(order_data.get("uuid"))
            if existing:
                return {"sale_order_id": existing.id}
            raise

        return {
            "sale_order_id": sale_order.id,
        }
