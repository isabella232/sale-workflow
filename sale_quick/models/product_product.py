# Copyright 2022 Camptocamp SA
# @author: Damien Crier <damien.crier@camptocamp.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    so_line_ids = fields.One2many(
        comodel_name="sale.order.line",
        inverse_name="product_id",
        help="Technical: used to compute quantities to sale.",
    )

    def _default_quick_uom_id(self):
        if self.env.context.get("parent_model", False) == "sale.order":
            return self.uom_id
        return super()._default_quick_uom_id()

    def _compute_process_qty_sale(self):
        groups = self.env["sale.order.line"].read_group(
            [("order_id", "=", self.env.context.get("parent_id"))],
            fields=["product_id", "product_uom_qty"],
            groupby=["product_id"],
        )
        quantities = {g["product_id"]: g["product_uom_qty"] for g in groups}
        for rec in self:
            rec.qty_to_process = quantities.get(rec.id, 0)

    @api.depends("so_line_ids")
    def _compute_process_qty(self):
        res = super(ProductProduct, self)._compute_process_qty()
        if self.env.context.get("parent_model", False) == "sale.order":
            self._compute_process_qty_sale()
        return res

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        sale = self.env["sale.order"].browse(self.env.context.get("parent_id"))
        if self.env.context.get("in_current_parent") and sale:
            so_lines = self.env["sale.order.line"].search([("order_id", "=", sale.id)])
            args.append(("id", "in", so_lines.mapped("product_id").ids))

        return super(ProductProduct, self).search(
            args, offset=offset, limit=limit, order=order, count=count
        )

    @api.model
    def check_access_rights(self, operation, raise_exception=True):
        """ hijack product edition rights if we're in the mass edition menu """
        if self.env.context.get("quick_access_rights_sale"):
            return self.env["sale.order.line"].check_access_rights(
                operation, raise_exception
            )
        return super().check_access_rights(operation, raise_exception)
