# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from collections import defaultdict

from odoo import models


class PricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    def _get_pricelist_products_group(self):
        """Returns a mapping of products grouped by pricelist.

        Result:
        keys: product.pricelist id
        values: product.product list of ids
        """
        pricelist_products = defaultdict(list)
        for item in self:
            pricelist_products[item.pricelist_id.id].append(item.product_id.id)
        return pricelist_products
