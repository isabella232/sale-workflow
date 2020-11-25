from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ProductCategory(models.Model):
    """Extend to add fields is_promotion_category/is_coupon_category."""

    _inherit = "product.category"

    is_promotion_category = fields.Boolean()
    is_coupon_category = fields.Boolean()
    default_promotion_next_order_category = fields.Boolean(copy=False)
    program_option_ids = fields.Many2many(
        "sale.coupon.program.option", string="Coupon/Promotion Options"
    )

    @api.onchange("is_promotion_category")
    def _onchange_is_promotion_category(self):
        if not self.is_promotion_category:
            self.default_promotion_next_order_category = False

    @api.constrains("program_option_ids")
    def _check_promotion_ids(self):
        for rec in self:
            rec.program_option_ids.validate_compatibility()

    def _predicate_product_categ_with_opts(self):
        # Expects empty or singleton record.
        return (
            self.is_promotion_category or self.is_coupon_category
        ) and self.program_option_ids

    @api.constrains("default_promotion_next_order_category")
    def _check_default_promotion_next_order_category(self):
        if self.filtered("default_promotion_next_order_category"):
            count = self.search_count(
                [("default_promotion_next_order_category", "=", True)]
            )
            if count > 1:
                raise ValidationError(
                    _("There can be only one Default Promotion Next Order Category")
                )
