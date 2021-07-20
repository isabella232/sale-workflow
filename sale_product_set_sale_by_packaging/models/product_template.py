# Copyright 2021 Camptocamp SA
# @author Simone Orsi <simone.orsi@camptocamp.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    # Just for UI purpose
    sell_only_by_packaging_prod_set_tocheck = fields.Boolean(
        help="If this flag is ON, "
        "it means you have to check all product.set associated with it",
        compute="_compute_sell_only_by_packaging_prod_set_tocheck",
    )

    @api.depends("sell_only_by_packaging")
    def _compute_sell_only_by_packaging_prod_set_tocheck(self):
        ids_to_check = self._product_ids_to_check()
        for rec in self:
            value = False
            if rec.sell_only_by_packaging and ids_to_check:
                value = set(rec.product_variant_ids.ids).intersection(ids_to_check)
            rec.sell_only_by_packaging_prod_set_tocheck = value

    def _product_ids_to_check(self):
        """Retrieves product.product IDS to check on product sets.
        """
        ids_to_check = self.filtered("sell_only_by_packaging").product_variant_ids.ids
        if not ids_to_check:
            return []
        query = """
            SELECT
                product_id
            FROM
                product_set_line
            WHERE
                product_id in (%s)
            AND
                product_packaging_id IS NULL
        """
        self.env["product.set.line"].flush(["product_id", "product_packaging_id"])
        self.env.cr.execute(query, (tuple(ids_to_check),))
        return [x[0] for x in self.env.cr.fetchall()]

    def action_view_product_set_lines_to_check(self):
        ids_to_check = self._product_ids_to_check()
        action = self.env.ref("sale_product_set.act_open_product_set_line_view")
        action_data = action.read()[0]
        action_data["domain"] = [("product_id", "in", ids_to_check)]
        return action_data
