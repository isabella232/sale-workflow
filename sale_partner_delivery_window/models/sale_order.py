# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import _, api, fields, models
from odoo.addons.partner_tz.tools import tz_utils


class SaleOrder(models.Model):

    _inherit = "sale.order"

    @api.depends(
        "partner_shipping_id.delivery_time_preference",
        "partner_shipping_id.delivery_time_window_ids",
        "partner_shipping_id.delivery_time_window_ids.start",
        "partner_shipping_id.delivery_time_window_ids.end",
        "partner_shipping_id.delivery_time_window_ids.weekday_ids",
    )
    def _compute_expected_date(self):
        """Add dependencies to consider fixed weekdays delivery schedule"""
        return super()._compute_expected_date()

    @api.onchange("commitment_date")
    def _onchange_commitment_date(self):
        """Warns if commitment date is not a preferred weekday for delivery"""
        res = super()._onchange_commitment_date()
        if res:
            return res
        if (
            self.commitment_date
            and self.partner_shipping_id.delivery_time_preference == "time_windows"
        ):
            ps = self.partner_shipping_id
            if not ps.is_in_delivery_window(self.commitment_date):
                user_tz = self.env.user.tz
                tz_commitment_date = tz_utils.utc_to_tz_naive_datetime(
                    user_tz, self.commitment_date
                )
                return {
                    "warning": {
                        "title": _(
                            "Commitment date does not match shipping "
                            "partner's Delivery time schedule preference."
                        ),
                        "message": _(
                            "The delivery date is %s, but the shipping "
                            "partner is set to prefer deliveries on following "
                            "time windows:\n%s"
                            % (
                                # TODO handle date format
                                tz_commitment_date,
                                '\n'.join(
                                    [
                                        "  * %s" % w.tz_display_name
                                        for w
                                        in ps.get_delivery_windows().get(ps.id)
                                    ]
                                ),
                            )
                        ),
                    }
                }


class SaleOrderLine(models.Model):

    _inherit = "sale.order.line"

    def _expected_date(self):
        """Postpone expected_date to next preferred weekday"""
        expected_date = super()._expected_date()
        partner = self.order_id.partner_shipping_id
        if partner.delivery_time_preference == "anytime":
            return expected_date
        return partner.next_delivery_window_start_datetime(
            from_date=expected_date
        )

    def _prepare_procurement_values(self, group_id=False):
        """Consider delivery_schedule in procurement"""
        res = super()._prepare_procurement_values(group_id=group_id)
        if (
            self.order_id.partner_shipping_id.delivery_time_preference != "time_windows"
            # if a commitment_date is set we don't change the result as lead
            # time and delivery week days must have been considered
            or self.order_id.commitment_date
        ):
            return res
        # If no commitment date is set, we must consider next preferred delivery
        #  weekday to postpone date_planned
        date_planned = fields.Datetime.to_datetime(res.get("date_planned"))
        ops = self.order_id.partner_shipping_id
        next_preferred_date = ops.next_delivery_window_start_datetime(
            from_date=date_planned
        )
        if next_preferred_date != date_planned:
            res["date_planned"] = next_preferred_date
        return res

    @api.depends(
        "order_id.expected_date"
    )
    def _compute_qty_at_date(self):
        """Trigger computation of qty_at_date when expected_date is updated"""
        return super()._compute_qty_at_date()
