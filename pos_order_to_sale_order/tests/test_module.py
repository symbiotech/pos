# Copyright (C) 2022-Today GRAP (http://www.grap.coop)
# @author Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo.tests import tagged

from odoo.addons.point_of_sale.tests.test_frontend import TestPointOfSaleHttpCommon


@tagged("post_install", "-at_install")
class TestUi(TestPointOfSaleHttpCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.whiteboard_pen.is_storable = True
        cls.wall_shelf.is_storable = True
        cls.pos_partner = cls.env["res.partner"].create(
            {
                "name": "Pos Partner",
                "is_company": False,
                "email": "let@it.be",
            }
        )
        cls.customer_account_payment_method = cls.env["pos.payment.method"].create(
            {
                "name": "Customer Account",
                "split_transactions": True,
            }
        )

    def _prepare_pos_for_tour(self):
        self.main_pos_config.with_user(self.pos_user).open_ui()

        # Make the test compatible with pos_minimize_menu
        if "iface_important_buttons" in self.main_pos_config._fields:
            self.main_pos_config.iface_important_buttons = ",".join(
                [
                    "CreateOrderButton",
                    "OrderlineCustomerNoteButton",
                ]
            )

    def _assert_invoiced_sale_order(self, order):
        self.assertAlmostEqual(
            order.amount_total,
            5.18,
            places=2,
            msg="Total Amount must be equal to 5.18",
        )
        self.assertEqual(order.state, "sale", "Order state must be equal to 'sale'")
        self.assertEqual(
            order.delivery_status, "full", "Delivery status must be equal to 'full'"
        )
        self.assertEqual(
            order.invoice_status,
            "invoiced",
            "Invoice status must be equal to 'invoiced'",
        )
        self.assertNotIn(
            "Product Note",
            order.order_line[0].name,
            "'Product Note' must not be in the first sale order line description",
        )
        self.assertIn(
            "Product Note",
            order.order_line[1].name,
            "'Product Note' must be in the second sale order line description",
        )

    def test_pos_order_to_sale_order(self):
        self._prepare_pos_for_tour()

        before_orders = self.env["sale.order"].search(
            [("partner_id", "=", self.pos_partner.id)],
            order="id",
        )

        self.start_tour(
            f"/pos/ui/{self.main_pos_config.id}",
            "PosOrderToSaleOrderTour",
            login="accountman",
        )

        after_orders = self.env["sale.order"].search(
            [("partner_id", "=", self.pos_partner.id)],
            order="id",
        )

        self.assertEqual(len(before_orders) + 1, len(after_orders))
        self._assert_invoiced_sale_order(after_orders[-1])

    def test_pos_order_to_sale_order_one_shot(self):
        self.main_pos_config.iface_create_sale_order_default = "invoiced"
        self._prepare_pos_for_tour()

        before_orders = self.env["sale.order"].search(
            [("partner_id", "=", self.pos_partner.id)],
            order="id",
        )

        self.start_tour(
            f"/pos/ui/{self.main_pos_config.id}",
            "PosOrderToSaleOrderOneShotTour",
            login="accountman",
        )

        after_orders = self.env["sale.order"].search(
            [("partner_id", "=", self.pos_partner.id)],
            order="id",
        )

        self.assertEqual(len(before_orders) + 1, len(after_orders))
        self._assert_invoiced_sale_order(after_orders[-1])

    def test_pos_order_to_sale_order_validate(self):
        self.main_pos_config.write(
            {
                "iface_create_sale_order_default": "invoiced",
                "iface_create_sale_order_on_validate": True,
                "payment_method_ids": [
                    (4, self.customer_account_payment_method.id),
                ],
            }
        )
        self._prepare_pos_for_tour()

        before_orders = self.env["sale.order"].search(
            [("partner_id", "=", self.pos_partner.id)],
            order="id",
        )
        before_pos_orders = self.env["pos.order"].search_count([])

        self.start_tour(
            f"/pos/ui/{self.main_pos_config.id}",
            "PosOrderToSaleOrderValidateTour",
            login="accountman",
        )

        after_orders = self.env["sale.order"].search(
            [("partner_id", "=", self.pos_partner.id)],
            order="id",
        )
        after_pos_orders = self.env["pos.order"].search_count([])

        self.assertEqual(len(before_orders) + 1, len(after_orders))
        self.assertEqual(
            before_pos_orders,
            after_pos_orders,
            "Customer Account Validate must not create a PoS order",
        )
        self._assert_invoiced_sale_order(after_orders[-1])
