# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)


from odoo.addons.pricelist_cache.tests.common import TestPricelistCacheCommon


class TestPricelistCacheHistoryCommon(TestPricelistCacheCommon):
    def check_duplicates(self):
        duplicates_query = """
            SELECT product_id, pricelist_id, count(*)
            FROM product_pricelist_cache
            WHERE date_start IS NULL and date_end IS NULL
            GROUP BY product_id, pricelist_id
            HAVING count(*) > 1;
        """
        self.env.cr.execute(duplicates_query)
        res = self.env.cr.fetchall()
        self.assertFalse(res)

    def assert_prices_equal(self, pricelist_id, product_prices):
        for product_id, prices in product_prices.items():
            for price, _date_start, _date_end in prices:
                cache = self.search_price(product_id, pricelist_id)
                self.assertEqual(cache.price, price)
