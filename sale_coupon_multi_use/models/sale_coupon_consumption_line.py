# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, fields, models
from odoo.exceptions import UserError


class SaleCouponConsumptionLine(models.Model):
    """Model that stores data for single coupon multiple uses."""

    _name = "sale.coupon.consumption_line"
    _description = "Sale Coupon Consumption Line"

    coupon_id = fields.Many2one("sale.coupon", "Coupon", required=True, index=True)
    # ondelete takes care of automatically removing consumption line,
    # when discount line is removed on related sale order.
    sale_order_line_id = fields.Many2one(
        "sale.order.line", "Sale Order Line", required=True, ondelete="cascade"
    )
    amount = fields.Float()

    def _normalize_discount(self):
        """Adjust SOL discount to match consumed discount."""
        self.ensure_one()
        # Discount initially won't match, when standard functionality
        # applies full discount from coupon. But because we split
        # coupon amount, we want to apply maximum possible discount.
        sol = self.sale_order_line_id
        sol_discount = abs(sol.price_unit)
        amount_to_adjust = sol_discount - self.amount
        if amount_to_adjust > 0:
            # Reducing negative amount here.
            sol.price_unit += amount_to_adjust

    def unlink(self):
        """Override to prevent direct unlink."""
        if not self._context.get("force_unlink_coupon_consumption_lines"):
            raise UserError(
                _(
                    "Consumption Lines can't be deleted directly. To do that, "
                    "delete related sale order line."
                )
            )
        return super().unlink()
