# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.addons.sale_coupon_multi_currency.tests.common import (
    TestSaleCouponMultiCurrencyCommon,
)


class TestSaleCouponMultiUseCommon(TestSaleCouponMultiCurrencyCommon):
    """Common class for multi use coupon tests."""

    @classmethod
    def setUpClass(cls):
        """Set up common data for multi use coupon tests."""
        super().setUpClass()
        # Models.
        cls.SaleCoupon = cls.env["sale.coupon"]
        cls.SaleCouponProgram = cls.env["sale.coupon.program"]
        cls.SaleCouponGenerate = cls.env["sale.coupon.generate"]
        cls.SaleCouponApplyCode = cls.env["sale.coupon.apply.code"]
        # Sales.
        # amount_total = 9705
        cls.sale_1 = cls.env.ref("sale.sale_order_1")
        # amount_total = 2947.5
        cls.sale_2 = cls.env.ref("sale.sale_order_2")
