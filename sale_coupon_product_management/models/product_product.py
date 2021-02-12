# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ProductProduct(models.Model):

    _inherit = "product.product"

    program_product_sale_ok = fields.Boolean(
        related="categ_id.program_product_sale_ok"
    )
    program_product_discount_fixed_amount = fields.Boolean(
        related="categ_id.program_product_discount_fixed_amount"
    )

    @api.onchange("categ_id")
    def _onchange_program_categ_id(self):
        category = self.categ_id
        if category.is_program_category:
            self.sale_ok = self.program_product_sale_ok
            # In case of existing product, we don't reset the price.
            if self.program_product_discount_fixed_amount and not self.id.origin:
                self.lst_price = False
