# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo.tests.common import SavepointCase

OPTION_XMLID_PREFIX = (
    "sale_coupon_product_management.sale_coupon_program_option_coupon_"
)


class TestSaleCouponProductManageCommon(SavepointCase):
    """Common class for program product tests."""

    @classmethod
    def setUpClass(cls):
        """Set up common data for multi use coupon tests."""
        super().setUpClass()
        # Models.
        cls.SaleCoupon = cls.env["sale.coupon"]
        cls.SaleCouponProgram = cls.env["sale.coupon.program"]
        cls.SaleCouponGenerate = cls.env["sale.coupon.generate"]
        cls.SaleCouponApplyCode = cls.env["sale.coupon.apply.code"]
        cls.ProductCategory = cls.env["product.category"]
        # Records.
        # Coupon Programs.
        cls.program_coupon_percentage = cls.env.ref("sale_coupon.10_percent_coupon")
        # Coupon Program Options.
        cls.program_option_fixed_amount = cls.env.ref(
            "{}{}".format(OPTION_XMLID_PREFIX, "discount_fixed_amount")
        )
        cls.program_option_sale_ok = cls.env.ref(
            "{}{}".format(OPTION_XMLID_PREFIX, "product_sale_ok")
        )
        cls.program_option_not_sale_ok = cls.env.ref(
            "{}{}".format(OPTION_XMLID_PREFIX, "product_not_sale_ok")
        )
        # Sales.
        # amount_total = 9705
        cls.sale_1 = cls.env.ref("sale.sale_order_1")
        # amount_total = 2947.5
        cls.sale_2 = cls.env.ref("sale.sale_order_2")
