# Copyright (C) 2017 - Today: GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models
from odoo.exceptions import ValidationError

_CREATE_SALE_ORDER_DEFAULT_FLAGS = {
    "draft": "iface_create_draft_sale_order",
    "confirmed": "iface_create_confirmed_sale_order",
    "delivered": "iface_create_delivered_sale_order",
    "invoiced": "iface_create_invoiced_sale_order",
}


class PosConfig(models.Model):
    _inherit = "pos.config"

    iface_create_sale_order = fields.Boolean(
        string="Create Sale Orders",
        compute="_compute_iface_create_sale_order",
        store=True,
    )

    iface_create_draft_sale_order = fields.Boolean(
        string="Create Draft Sale Orders",
        default=True,
        help="If checked, the cashier will have the possibility to create"
        " a draft Sale Order, based on the current draft PoS Order.",
    )

    iface_create_confirmed_sale_order = fields.Boolean(
        string="Create Confirmed Sale Orders",
        default=True,
        help="If checked, the cashier will have the possibility to create"
        " a confirmed Sale Order, based on the current draft PoS Order.",
    )

    iface_create_delivered_sale_order = fields.Boolean(
        string="Create Delivered Sale Orders",
        default=True,
        help="If checked, the cashier will have the possibility to create"
        " a confirmed Sale Order, based on the current draft PoS Order.\n"
        "The corresponding picking will be marked as delivered. Only invoice"
        " processing will be possible.",
    )

    iface_create_invoiced_sale_order = fields.Boolean(
        string="Create Invoiced Sale Orders",
        default=True,
        help="If checked, the cashier will have the possibility to create"
        " a confirmed Sale Order, based on the current draft PoS Order.\n"
        "The corresponding picking will be marked as delivered.\n"
        "The invoice will be generated and confirmed.\n"
        "Only invoice payment processing will be possible.",
    )

    iface_create_sale_order_default = fields.Selection(
        selection=[
            ("ask", "Ask"),
            ("draft", "Draft"),
            ("confirmed", "Confirmed"),
            ("delivered", "Delivered"),
            ("invoiced", "Invoiced"),
        ],
        string="Default Sale Order Creation",
        default="ask",
        required=True,
        help="If set to a specific state, the Create Order button creates a"
        " Sale Order in that state without asking. If set to Ask, the cashier"
        " chooses the state in a popup.\n"
        "When Create Sale Order on Customer Account Validate is enabled,"
        " Ask is not allowed and Validate uses this default state.",
    )

    iface_create_sale_order_on_validate = fields.Boolean(
        string="Create Sale Order on Customer Account Validate",
        default=False,
        help="If checked, paying fully with Customer Account and clicking"
        " Validate creates a Sale Order in the Default Sale Order Creation"
        " state and shows a receipt. No Point of Sale order is saved."
        " Default Sale Order Creation must not be Ask.",
    )

    @api.depends(
        "iface_create_draft_sale_order",
        "iface_create_confirmed_sale_order",
        "iface_create_delivered_sale_order",
        "iface_create_invoiced_sale_order",
    )
    def _compute_iface_create_sale_order(self):
        for config in self:
            config.iface_create_sale_order = any(
                [
                    config.iface_create_draft_sale_order,
                    config.iface_create_confirmed_sale_order,
                    config.iface_create_delivered_sale_order,
                    config.iface_create_invoiced_sale_order,
                ]
            )

    @api.onchange(
        "iface_create_draft_sale_order",
        "iface_create_confirmed_sale_order",
        "iface_create_delivered_sale_order",
        "iface_create_invoiced_sale_order",
        "iface_create_sale_order_default",
        "iface_create_sale_order_on_validate",
    )
    def _onchange_iface_create_sale_order_default(self):
        for config in self:
            flag = _CREATE_SALE_ORDER_DEFAULT_FLAGS.get(
                config.iface_create_sale_order_default
            )
            if flag and not config[flag]:
                config.iface_create_sale_order_default = "ask"
            if (
                config.iface_create_sale_order_on_validate
                and config.iface_create_sale_order_default == "ask"
            ):
                config.iface_create_sale_order_default = (
                    config._get_first_enabled_create_sale_order_state()
                )

    def _get_first_enabled_create_sale_order_state(self):
        self.ensure_one()
        for state, flag in _CREATE_SALE_ORDER_DEFAULT_FLAGS.items():
            if self[flag]:
                return state
        return "ask"

    @api.constrains(
        "iface_create_draft_sale_order",
        "iface_create_confirmed_sale_order",
        "iface_create_delivered_sale_order",
        "iface_create_invoiced_sale_order",
        "iface_create_sale_order_default",
        "iface_create_sale_order_on_validate",
    )
    def _check_iface_create_sale_order_default(self):
        for config in self:
            flag = _CREATE_SALE_ORDER_DEFAULT_FLAGS.get(
                config.iface_create_sale_order_default
            )
            if flag and not config[flag]:
                raise ValidationError(
                    self.env._(
                        "The default Sale Order Creation must match an enabled"
                        " creation option, or be set to Ask."
                    )
                )
            if (
                config.iface_create_sale_order_on_validate
                and config.iface_create_sale_order_default == "ask"
            ):
                raise ValidationError(
                    self.env._(
                        "Default Sale Order Creation cannot be Ask when Create"
                        " Sale Order on Customer Account Validate is enabled."
                    )
                )
