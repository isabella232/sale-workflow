# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from itertools import groupby

from psycopg2 import sql

from odoo import fields, models


class PricelistCache(models.Model):

    _inherit = "product.pricelist.cache"

    date_start = fields.Date(index=True)
    date_end = fields.Date(index=True)

    def _get_update_values(self, product_prices):
        # As implementation of `product_pricelist._get_product_prices` have changed
        # we need to rewrite this completely.
        return [
            sql.SQL(", ").join(
                map(
                    sql.Literal, (record.id, product_prices[record.product_id.id][0][0])
                )
            )
            for record in self
        ]

    def _get_update_query(self):
        return sql.SQL(
            """
            UPDATE
                product_pricelist_cache AS pricelist_cache
            SET
                price = c.price
            FROM (VALUES ({}))
                AS c(id, price)
            WHERE c.id = pricelist_cache.id
            AND pricelist_cache.date_start IS NULL
            AND pricelist_cache.date_end IS NULL;
            """
        )

    def _get_create_values(self, pricelist_id, product_ids, product_prices):
        values = []
        for product_id in product_ids:
            prices = product_prices.get(product_id)
            # Be defensive here
            if not prices:
                continue
            for (price, date_start, date_end) in prices:
                values.append(
                    sql.SQL(", ").join(
                        map(
                            sql.Literal,
                            (
                                product_id,
                                pricelist_id,
                                price,
                                date_start or None,
                                date_end or None,
                            ),
                        )
                    )
                )
        return values

    def _get_create_query(self):
        return sql.SQL(
            """
            INSERT INTO product_pricelist_cache (
                product_id, pricelist_id, price, date_start, date_end
            )
            VALUES ({});
            """
        )

    def _get_existing_cache_domain(self, pricelist_id, product_ids):
        # If a pricelist item with date range has changed during the day,
        # it would be complicated to retrieve the original record.
        # Exclude those items, so they are re-created.
        # It will be reset at cron execution anyway…
        res = super()._get_existing_cache_domain(pricelist_id, product_ids)
        res.extend([("date_start", "=", False), ("date_end", "=", False)])
        return res

    def _get_cached_prices_domain(self, pricelist, products, **kwargs):
        at_date = kwargs.get("at_date")
        if not at_date:
            at_date = fields.Date.today()
        return [
            ("pricelist_id", "=", pricelist.id),
            ("product_id", "in", products.ids),
            "|",
            ("date_start", "=", False),
            ("date_start", "<=", at_date),
            "|",
            ("date_end", "=", False),
            ("date_end", ">=", at_date),
        ]

    def get_cached_prices_for_pricelist(self, pricelist, products, **kwargs):
        """Retrieves product prices for a given pricelist."""
        cached_prices = super().get_cached_prices_for_pricelist(
            pricelist, products, **kwargs
        )
        # For each product, we might have multiple cached prices here.
        # For instance, there could be a price with no dates and another one with.
        # Filter the cached prices here, prioritize those who have a date range.
        return cached_prices.remove_duplicates()

    def remove_duplicates(self):
        cache_ids = set()
        self.sorted("product_id")
        for _, cache_group in groupby(self, key=lambda r: r.product_id):
            cache_list = list(cache_group)
            if len(cache_list) > 1:
                # look for the first cache item with date.
                # return the first one without otherwise.
                for cache_item in cache_list:
                    if cache_item.date_start or cache_item.date_end:
                        cache_ids.add(cache_item.id)
                        break
                else:
                    cache_ids.add(cache_list[0].id)
            else:
                cache_ids.add(cache_list[0].id)
        return self.browse(cache_ids)

    def _get_tree_view(self, domain=None):
        xmlid = "pricelist_cache.product_pricelist_cache_action"
        action = self.env["ir.actions.act_window"]._for_xml_id(xmlid)
        if domain is not None:
            action["domain"] = domain
        return action
