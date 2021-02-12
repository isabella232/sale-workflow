# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class SaleCouponProgram(models.Model):
    """Extend to improve product related product management."""

    _inherit = "sale.coupon.program"

    force_product_default_code = fields.Char()
    force_product_categ_id = fields.Many2one(
        comodel_name="product.category",
        domain=[('is_program_category', '=', True)]
    )
    discount_line_product_chosen = fields.Boolean()

    @api.onchange("program_type", "promo_applicability")
    def _onchange_promo_applicability(self):
        if (
            self.program_type == "promotion_program"
            and self.promo_applicability == "on_next_order"
            and not self.force_product_categ_id
        ):
            # If several default categories found, just take the first
            default_categ = self.env["product.category"].search(
                [("default_promotion_next_order_category", "=", True)], limit=1
            )
            if default_categ:
                self.force_product_categ_id = default_categ.id

    @api.onchange("discount_line_product_chosen")
    def _onchange_discount_line_product_chosen(self):
        for rec in self:
            rec.force_product_default_code = False

    @api.onchange("force_product_categ_id")
    def _onchange_force_product_categ_id(self):
        for rec in self:
            rec.discount_line_product_id = False

    @api.constrains("force_product_categ_id", "reward_type", "discount_type")
    def _check_program_options(self):
        for rec in self:
            category = rec.force_product_categ_id
            if (
                category.program_product_discount_fixed_amount
                and not (rec.reward_type == "discount" and rec.discount_type == "fixed_amount")
            ):
                raise UserError(_(
                    "With 'program_product_discount_fixed_amount' category, "
                    "the reward type must be 'discount' and "
                    "the discount type must be 'Fixed Amount'."
                ))

    def _check_no_product_duplicate(self):
        for rec in self:
            other_program_found = self.search_count([
                ("discount_line_product_id", "=", rec.discount_line_product_id.id),
                ("id", "!=", rec.id),
            ])
            if other_program_found:
                raise UserError(_(
                    "This reward line product is already used "
                    "into another program."
                ))

    def _force_values_on_product(self):
        product = self.discount_line_product_id
        if product.categ_id != self.force_product_categ_id:
            product.categ_id = self.force_product_categ_id
            product._onchange_program_categ_id()
        if not self.discount_line_product_chosen:
            product.name = self.name
        if self.force_product_categ_id.program_product_discount_fixed_amount:
            product.lst_price = self.discount_fixed_amount  # Marche pas quand créé à la volée
        if self.force_product_default_code:
            product.default_code = self.force_product_default_code

    @api.model
    def create(self, vals):
        program = super().create(vals)
        if program.discount_line_product_chosen:
            program._check_no_product_duplicate()
        else:
            program._force_values_on_product()
        return program

    def write(self, vals):
        result = super().write(vals)
        for program in self:
            if not program.discount_line_product_chosen:
                if not program.discount_line_product_id:
                    product = self.env['product.product'].create({
                        "name": program.name,
                        "categ_id": program.force_product_categ_id.id,
                        "type": "service",
                        "taxes_id": False,
                        "supplier_taxes_id": False,
                        "sale_ok": False,
                        "purchase_ok": False,
                        "invoice_policy": "order",
                        "lst_price": 0,
                    })
                    program.discount_line_product_id = product
                program._force_values_on_product()
            program._check_no_product_duplicate()
        return result
