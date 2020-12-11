# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import api, fields, models


class ProductPackaging(models.Model):
    _inherit = "product.packaging"

    can_be_sold = fields.Boolean(string="Can be sold")

    @api.model_create_multi
    def create(self, vals_list):
        packagings = super().create(vals_list)
        for pack in packagings:
            pack.write({"can_be_sold": pack.packaging_type_id.can_be_sold})
        return packagings
