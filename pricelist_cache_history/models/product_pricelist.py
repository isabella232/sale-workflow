# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from collections import defaultdict
from datetime import date

from odoo import models


class Pricelist(models.Model):
    _inherit = "product.pricelist"

    def _get_date_by_product(self, product_ids):
        # The idea here is to retrieve the date before any pricelist item was applied
        # for a given product / pricelist configuration, if there's no item with
        # a date_start, return the date as of today
        res = []
        if product_ids:
            query = """
                SELECT MIN(date_start) - INTERVAL '1 DAY', ARRAY_AGG(product_id)
                FROM product_pricelist_item
                WHERE date_start IS NOT NULL
                AND pricelist_id = %(pricelist_id)s
                AND product_id IN %(product_ids)s
                GROUP BY product_id, date_start;
            """
            self.env.cr.execute(
                query, {"pricelist_id": self.id, "product_ids": tuple(product_ids)}
            )
            res = self.env.cr.fetchall()
        # Retrieve product ids where no date_start has been found
        product_ids_with_date_start = set().union(*[p_ids for _, p_ids in res])
        product_ids_without_date_start = set(product_ids) - product_ids_with_date_start
        res.append((date.today(), list(product_ids_without_date_start)))
        return res

    def _get_product_prices(self, product_ids):
        # In the pricelist_cache implementation, the returned prices were those of
        # `today`. Here we need to cache the base price, then the price with date
        # ranges.
        # The base price is the price that isn't altered by pricelist items with
        # a date range.
        # In order to not waste resources, completely override the previous implementation
        # as `_compute_price_rule` takes a lot of time.
        self.ensure_one()
        # Search instead of browse, since products could have been unlinked
        # between the time where records have been created / modified
        # and the time this method is executed.
        # TODO
        # 3 cases to handle here:
        # - items with date start but no date end
        # - items with date end but bo date start
        # - items with both date_start and date_end
        product_prices = defaultdict(list)
        for day_without_item, p_ids in self._get_date_by_product(product_ids):
            products = self.env["product.product"].search([("id", "in", p_ids)])
            products_qty_partner = [(p, 1, False) for p in products]
            results = self._compute_price_rule(products_qty_partner, day_without_item)
            for prod, price in results.items():
                product_prices[prod].append((price[0], False, False))
        # Now, also store prices with date range
        items_with_date_range = self.item_ids.filtered(
            lambda i: i._has_date_range() and i.product_id.id in product_ids
        )
        for item in items_with_date_range:
            # for each item, get the price at the given date range
            # TODO group by date
            product_id = item.product_id.id
            at_date = item.date_start or item.date_end
            price = self._compute_price_rule([(item.product_id, 1, False)], at_date)
            product_prices[product_id].append(
                (price[product_id][0], item.date_start, item.date_end)
            )
        return product_prices
