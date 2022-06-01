# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import api, fields, models


class PricelistCacheWizard(models.TransientModel):
    _inherit = "product.pricelist.cache.wizard"

    at_date = fields.Date()

    @api.onchange("pricelist_id", "product_id", "at_date")
    def _onchange_product_pricelist(self):
        return super()._onchange_product_pricelist()

    @api.model
    def _get_cached_prices(self, products):
        cache_model = self.env["product.pricelist.cache"]
        return cache_model.get_cached_prices_for_pricelist(
            self.pricelist_id, products, at_date=self.at_date
        )
