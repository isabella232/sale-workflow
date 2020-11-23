from odoo import models


class SaleOrder(models.Model):
    """Extend to modify action_confirm for multi-use coupons."""

    _inherit = "sale.order"

    def action_confirm(self):
        """Extend to pass coupon_order_data context."""
        for order in self:
            order = order.with_context(coupon_sale_order=order)
            super(SaleOrder, order).action_confirm()
        return True
