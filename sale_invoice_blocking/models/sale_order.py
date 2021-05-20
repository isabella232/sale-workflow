# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    invoice_blocking_reason_id = fields.Many2one(
        "invoice.blocking.reason",
        string="Blocking for invoicing",
    )
