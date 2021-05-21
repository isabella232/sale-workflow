# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    invoice_blocking_reason_id = fields.Many2one(
        "invoice.blocking.reason",
        string="Blocking for invoicing",
    )

    @api.depends('invoice_blocking_reason_id', 'state', 'order_line.invoice_status')
    def _get_invoice_status(self):
        super()._get_invoice_status()
        unconfirmed_orders = self.filtered(
            lambda so: so.state not in ['sale', 'done'])
        unconfirmed_orders.invoice_status = 'no'
        confirmed_orders = self - unconfirmed_orders
        if not confirmed_orders:
            return

        for order in confirmed_orders:
            if order.invoice_blocking_reason_id:
                order.invoice_status = 'no'

    @api.model
    def _nothing_to_invoice_error(self):
        error = super()._nothing_to_invoice_error()
        msg = [x for x in error.args]

        msg.append(_("""
- You may have an invoice blocking reason on the sale order
        """))
        return UserError(msg)
