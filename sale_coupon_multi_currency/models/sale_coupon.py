from odoo import fields, models


class SaleCoupon(models.Model):
    """Extend to add related currency field."""

    _inherit = "sale.coupon"

    currency_program_id = fields.Many2one(related="program_id.currency_id")
