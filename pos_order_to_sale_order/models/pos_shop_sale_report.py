from odoo import api, fields, models, tools


class PosShopSaleReport(models.Model):
    _name = "pos.shop.sale.report"
    _description = "Shop Sales (POS + Sale Orders)"
    _auto = False
    _order = "date_order desc, id desc"

    name = fields.Char(string="Document", readonly=True)
    date_order = fields.Datetime(string="Order Date", readonly=True)
    date = fields.Date(readonly=True)
    source = fields.Selection(
        selection=[
            ("pos", "Point of Sale"),
            ("sale", "Sale Order"),
        ],
        readonly=True,
    )
    partner_id = fields.Many2one(
        comodel_name="res.partner", string="Customer", readonly=True
    )
    user_id = fields.Many2one(
        comodel_name="res.users", string="Salesperson", readonly=True
    )
    pos_session_id = fields.Many2one(
        comodel_name="pos.session", string="PoS Session", readonly=True
    )
    company_id = fields.Many2one(
        comodel_name="res.company", string="Company", readonly=True
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency", string="Currency", readonly=True
    )
    amount_total = fields.Monetary(
        string="Total", readonly=True, currency_field="currency_id"
    )
    pos_order_id = fields.Many2one(
        comodel_name="pos.order", string="PoS Order", readonly=True
    )
    sale_order_id = fields.Many2one(
        comodel_name="sale.order", string="Sale Order", readonly=True
    )

    def action_open_document(self):
        self.ensure_one()
        if self.pos_order_id:
            return {
                "type": "ir.actions.act_window",
                "res_model": "pos.order",
                "res_id": self.pos_order_id.id,
                "view_mode": "form",
                "target": "current",
            }
        return {
            "type": "ir.actions.act_window",
            "res_model": "sale.order",
            "res_id": self.sale_order_id.id,
            "view_mode": "form",
            "target": "current",
        }

    @api.model
    def _select_pos(self):
        return """
            SELECT
                po.id AS id,
                po.name AS name,
                po.date_order AS date_order,
                CAST(po.date_order AS date) AS date,
                'pos' AS source,
                po.partner_id AS partner_id,
                po.user_id AS user_id,
                po.session_id AS pos_session_id,
                po.company_id AS company_id,
                pc.currency_id AS currency_id,
                po.amount_total AS amount_total,
                po.id AS pos_order_id,
                NULL::integer AS sale_order_id
            FROM pos_order po
            JOIN pos_config pc ON pc.id = po.config_id
            WHERE po.state IN ('paid', 'done')
        """

    @api.model
    def _select_sale(self):
        return """
            SELECT
                -so.id AS id,
                so.name AS name,
                so.date_order AS date_order,
                CAST(so.date_order AS date) AS date,
                'sale' AS source,
                so.partner_id AS partner_id,
                so.user_id AS user_id,
                so.pos_session_id AS pos_session_id,
                so.company_id AS company_id,
                so.currency_id AS currency_id,
                so.amount_total AS amount_total,
                NULL::integer AS pos_order_id,
                so.id AS sale_order_id
            FROM sale_order so
            WHERE so.pos_session_id IS NOT NULL
                AND so.state != 'cancel'
        """

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(
            f"""
            CREATE OR REPLACE VIEW {self._table} AS (
                {self._select_pos()}
                UNION ALL
                {self._select_sale()}
            )
            """
        )
