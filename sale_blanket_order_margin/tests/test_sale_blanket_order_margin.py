from datetime import date, timedelta

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import common


class TestSaleBlanketOrders(common.TransactionCase):
    def setUp(self):
        super().setUp()
        self.blanket_order_obj = self.env["sale.blanket.order"]
        self.blanket_order_line_obj = self.env["sale.blanket.order.line"]
        self.blanket_order_wiz_obj = self.env["sale.blanket.order.wizard"]
        self.so_obj = self.env["sale.order"]

        self.payment_term = self.env.ref("account.account_payment_term_immediate")
        self.sale_pricelist = self.env["product.pricelist"].create(
            {"name": "Test Pricelist", "currency_id": self.env.ref("base.USD").id}
        )

        # UoM
        self.categ_unit = self.env.ref("uom.product_uom_categ_unit")
        self.uom_dozen = self.env["uom.uom"].create(
            {
                "name": "Test-DozenA",
                "category_id": self.categ_unit.id,
                "factor_inv": 12,
                "uom_type": "bigger",
                "rounding": 0.001,
            }
        )

        self.partner = self.env["res.partner"].create(
            {
                "name": "TEST CUSTOMER",
                "property_product_pricelist": self.sale_pricelist.id,
            }
        )

        self.product = self.env["product.product"].create(
            {
                "name": "Demo",
                "categ_id": self.env.ref("product.product_category_1").id,
                "standard_price": 35.0,
                "type": "consu",
                "uom_id": self.env.ref("uom.product_uom_unit").id,
                "default_code": "PROD_DEL01",
            }
        )
        self.product2 = self.env["product.product"].create(
            {
                "name": "Demo 2",
                "categ_id": self.env.ref("product.product_category_1").id,
                "standard_price": 50.0,
                "type": "consu",
                "uom_id": self.env.ref("uom.product_uom_unit").id,
                "default_code": "PROD_DEL02",
            }
        )

        self.yesterday = date.today() - timedelta(days=1)
        self.tomorrow = date.today() + timedelta(days=1)
