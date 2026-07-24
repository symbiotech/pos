# Copyright (C) 2017 - Today: GRAP (http://www.grap.coop)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class PosSession(models.Model):
    _inherit = "pos.session"

    sale_order_ids = fields.One2many(
        comodel_name="sale.order",
        inverse_name="pos_session_id",
        string="Sale Orders",
    )
    shop_sale_amount_total = fields.Monetary(
        string="Shop Sales Amount",
        compute="_compute_shop_sale_totals",
        currency_field="currency_id",
        help="Total of paid PoS orders and non-cancelled sale orders "
        "linked to this session.",
    )
    shop_sale_order_count = fields.Integer(
        string="Shop Sales Count",
        compute="_compute_shop_sale_totals",
        help="Number of paid PoS orders and non-cancelled sale orders "
        "linked to this session.",
    )

    @api.depends(
        "order_ids.state",
        "order_ids.amount_total",
        "sale_order_ids.state",
        "sale_order_ids.amount_total",
    )
    def _compute_shop_sale_totals(self):
        if not self.ids:
            for session in self:
                session.shop_sale_order_count = 0
                session.shop_sale_amount_total = 0.0
            return
        PosOrder = self.env["pos.order"]
        SaleOrder = self.env["sale.order"]
        pos_totals = {
            session.id: (count, amount or 0.0)
            for session, amount, count in PosOrder._read_group(
                domain=[
                    ("session_id", "in", self.ids),
                    ("state", "in", ("paid", "done")),
                ],
                groupby=["session_id"],
                aggregates=["amount_total:sum", "__count"],
            )
        }
        sale_totals = {
            session.id: (count, amount or 0.0)
            for session, amount, count in SaleOrder._read_group(
                domain=[
                    ("pos_session_id", "in", self.ids),
                    ("state", "!=", "cancel"),
                ],
                groupby=["pos_session_id"],
                aggregates=["amount_total:sum", "__count"],
            )
        }
        for session in self:
            pos_count, pos_amount = pos_totals.get(session.id, (0, 0.0))
            sale_count, sale_amount = sale_totals.get(session.id, (0, 0.0))
            session.shop_sale_order_count = pos_count + sale_count
            session.shop_sale_amount_total = pos_amount + sale_amount
