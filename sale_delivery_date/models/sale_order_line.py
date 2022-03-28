# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

import logging
from datetime import datetime, time, timedelta

import pytz

from odoo import api, fields, models

from odoo.addons.partner_tz.tools import tz_utils

_logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    """This override adds delays to the date_deadline and the date_planned.
    As per this commit 57f805f71e9357870dfc2498c5ef72ebd8ab7273
    - On pickings, the date_deadline represents the delivery date, and the
      date_planned represents the preparation date (date_deadline - security_lead).
    - On sale orders, date_planned represents the delivery date.
    """

    _inherit = "sale.order.line"

    def _prepare_procurement_values(self, group_id=False):
        # Here, we need to set date_deadline and date_planned correctly
        # res["date_planned"] is order.date_order + lead_time
        # So, date_planned should be:
        # date_planned - lead, on which we apply the cutoff and then the workload with
        # respect to the calendar (if any)
        # Also, date_deadline should be:
        # date_planned on which we apply the customer's time windows
        res = super()._prepare_procurement_values(group_id=group_id)
        # There's 2 cases here:
        # 1) commitment date is set, compute date_planned from date_deadline
        # 2) commitment date isn't set, compute date_planned and date_deadline
        if self.order_id.commitment_date:
            res = self._prepare_procurement_values_commitment_date(res)
        else:
            res = self._prepare_procurement_values_no_commitment_date(res)
        return res

    def _prepare_procurement_values_commitment_date(res):
        # 1) commitment_date - security_lead = order ready to be shipped (1)
        # 2) {1} - workload
        # 3) while {2} isn't a working day, remove 1 day
        # 4) apply cutoff (with `keep_same_day` param)
        return res

    def _prepare_procurement_values_no_commitment_date(res):
        # 1) apply cutoff -> saturday @ 9:00
        # 2) apply wh workload (2 days delay (duration vs days)) -> monday @ 17h00
        # while not working_day:
        # date - 1 day
        # apply cutoff -> monday @ 9h00 - timedelta(security_lead)
        # -> date_planned @ friday @ 9h00
        # 2.5) tuesday @ 17h00 # Add security_lead
        # 3) apply customer time window -> friday @ 9:00
        customer_lead, security_lead, workload = self._get_delays()
        res = self._remove_delays_prepare_procurement_values(res)
        res = self._cutoff_time_delivery_prepare_procurement_values(res)
        res = self._warehouse_calendar_prepare_procurement_values(res)
        res = self._delivery_window_prepare_procurement_values(res)
        return res

    def _remove_delays_prepare_procurement_values(self, res):
        date_planned = res.get("date_planned")
        _, _, workload = self._get_delays()
        if date_planned:
            new_date_planned = date_planned - timedelta(days=workload)
            res["date_planned"] = new_date_planned
            res["date_deadline"] = new_date_planned
        return res

    def _cutoff_time_delivery_prepare_procurement_values(self, res):
        date_planned = res.get("date_planned")
        if not date_planned:
            return res
        new_date_planned = self._prepare_procurement_values_cutoff_time(
            fields.Datetime.to_datetime(date_planned),
            # if we have a commitment date, even if we are too late, respect
            # the original planned date (but change the time), the transfer
            # will be considered as "late"
            keep_same_day=bool(self.order_id.commitment_date),
        )
        if new_date_planned:
            # TODO check if we have to update the date_deadline field
            # when commitment_date is set
            res["date_planned"] = new_date_planned
            res["date_deadline"] = new_date_planned
        return res

    def _warehouse_calendar_prepare_procurement_values(self, res):
        date_planned = res.get("date_planned")
        calendar = self.order_id.warehouse_id.calendar2_id
        if date_planned and calendar:
            customer_lead, security_lead, workload = self._get_delays()
            # plan_days() expect a number of days instead of a delay
            workload_days = self._delay_to_days(workload)
            td_workload = timedelta(days=workload)
            date_planned_w_workload = calendar.plan_days(
                workload_days, date_planned, compute_leaves=True
            )
            date_planned_w_sec_lead = date_planned_w_workload + timedelta(
                days=security_lead
            )
            res["date_planned"] = date_planned_w_workload
            res["date_deadline"] = date_planned_w_sec_lead
        return res

    def _delivery_window_prepare_procurement_values(self, res):
        date_planned = res.get("date_planned")
        date_deadline = res.get("date_deadline")
        if not date_deadline and not date_planned:
            return res
        # as we haven't yet updated date deadline, throw the date planned
        new_date_deadline = self._prepare_procurement_values_time_windows(
            fields.Datetime.to_datetime(date_planned)
        )
        if new_date_deadline:
            res["date_deadline"] = new_date_deadline
        return res

    def _prepare_procurement_values_time_windows(self, date_planned):
        # ORIGINAL
        if (
            self.order_id.partner_shipping_id.delivery_time_preference != "time_windows"
            # if a commitment_date is set we don't change the result as lead
            # time and delivery windows must have been considered
            or self.order_id.commitment_date
        ):
            _logger.debug(
                "Commitment date set on order %s. Delivery window not applied "
                "on line.",
                self.order_id.name,
            )
            return
        # If no commitment date is set, we must consider next preferred delivery
        #  window to postpone date_planned

        # Remove security lead time to ensure the delivery date (and not the
        # date planned of the picking) will match delivery windows
        date_planned_without_sec_lead = date_planned + timedelta(
            days=self.order_id.company_id.security_lead
        )
        ops = self.order_id.partner_shipping_id
        next_preferred_date = ops.next_delivery_window_start_datetime(
            from_date=date_planned_without_sec_lead
        )
        # Add back security lead time
        next_preferred_date_with_sec_lead = next_preferred_date - timedelta(
            days=self.order_id.company_id.security_lead
        )
        if date_planned != next_preferred_date_with_sec_lead:
            _logger.debug(
                "Delivery window applied for order %s. Date planned for line %s"
                " rescheduled from %s to %s",
                self.order_id.name,
                self.name,
                date_planned,
                next_preferred_date_with_sec_lead,
            )
            # if we have a new datetime proposed by a delivery time window,
            # apply the warehouse/partner cutoff time
            cutoff_datetime = self._prepare_procurement_values_cutoff_time(
                next_preferred_date_with_sec_lead,
                # the correct day has already been computed, only change
                # the cut-off time
                keep_same_day=True,
            )
            if cutoff_datetime:
                return cutoff_datetime
            return next_preferred_date_with_sec_lead
        else:
            _logger.debug(
                "Delivery window not applied for order %s. Date planned for line %s",
                " already in delivery window",
                self.order_id.name,
                self.name,
            )
        return

    def _delay_to_days(self, number_of_days):
        """Converts a delay to a number of days."""
        return number_of_days + 1

    def _get_delays(self):
        # customer_lead is security_lead + workload, as explained on the field
        customer_lead = self.customer_lead or 0.0
        security_lead = self.company_id.security_lead or 0.0
        workload = customer_lead - security_lead
        return customer_lead, security_lead, workload

    def _expected_date(self):
        # Computes the expected date with respect to the WH calendar, if any.
        expected_date = super()._expected_date()
        expected_date = self._cutoff_time_delivery_expected_date(expected_date)
        expected_date = self._warehouse_calendar_expected_date(expected_date)
        expected_date = self._delivery_window_expected_date(expected_date)
        return expected_date

    def _warehouse_calendar_expected_date(self, expected_date):
        calendar = self.order_id.warehouse_id.calendar2_id
        if calendar:
            customer_lead, security_lead, workload = self._get_delays()
            td_customer_lead = timedelta(days=customer_lead)
            td_security_lead = timedelta(days=security_lead)
            # plan_days() expect a number of days instead of a delay
            workload_days = self._delay_to_days(workload)
            # Remove customer_lead added to order_date in sale_stock
            expected_date -= td_customer_lead
            # Add the workload, with respect to the wh calendar
            expected_date = calendar.plan_days(
                workload_days, expected_date, compute_leaves=True
            )
            # add back the security lead
            expected_date += td_security_lead
        return expected_date

    def _delivery_window_expected_date(self, expected_date):
        partner = self.order_id.partner_shipping_id
        if not partner or partner.delivery_time_preference == "anytime":
            return expected_date
        return partner.next_delivery_window_start_datetime(from_date=expected_date)

    @api.depends("order_id.expected_date")
    def _compute_qty_at_date(self):
        """Trigger computation of qty_at_date when expected_date is updated"""
        return super()._compute_qty_at_date()

    def _prepare_procurement_values_cutoff_time(
        self, date_planned, keep_same_day=False
    ):
        """Apply the cut-off time on a planned date

        The cut-off configuration is taken on the partner if set, otherwise
        on the warehouse.

        By default, if the planned date is the same day but after the cut-off,
        the new planned date is delayed one day later. The argument
        keep_same_day forces keeping the same day.
        """
        cutoff = self.order_id.get_cutoff_time()
        partner = self.order_id.partner_shipping_id
        if not cutoff:
            if not self.order_id.warehouse_id.apply_cutoff:
                _logger.debug(
                    "No cutoff applied on order %s as partner %s is set to use "
                    "%s and warehouse %s doesn't apply cutoff."
                    % (
                        self.order_id,
                        partner,
                        partner.order_delivery_cutoff_preference,
                        self.order_id.warehouse_id,
                    )
                )
            else:
                _logger.warning(
                    "No cutoff applied on order %s. %s time not applied"
                    "on line %s."
                    % (self.order_id, partner.order_delivery_cutoff_preference, self)
                )
            return
        new_date_planned = self._get_utc_cutoff_datetime(
            cutoff, date_planned, keep_same_day
        )
        _logger.debug(
            "%s applied on order %s. Date planned for line %s"
            " rescheduled from %s to %s"
            % (
                partner.order_delivery_cutoff_preference,
                self.order_id,
                self,
                date_planned,
                new_date_planned,
            )
        )
        return new_date_planned

    def _cutoff_time_delivery_expected_date(self, expected_date):
        cutoff = self.order_id.get_cutoff_time()
        if not cutoff:
            return expected_date
        return self._get_utc_cutoff_datetime(cutoff, expected_date)

    def _get_utc_cutoff_datetime(self, cutoff, date, keep_same_day=False):
        tz = cutoff.get("tz")
        if tz:
            cutoff_time = time(hour=cutoff.get("hour"), minute=cutoff.get("minute"))
            # Convert here to naive datetime in UTC
            tz_loc = pytz.timezone(tz)
            tz_date = date.astimezone(tz_loc)
            tz_cutoff_datetime = datetime.combine(tz_date, cutoff_time)
            utc_cutoff_datetime = tz_utils.tz_to_utc_naive_datetime(
                tz_loc, tz_cutoff_datetime
            )
        else:
            utc_cutoff_datetime = date.replace(
                hour=cutoff.get("hour"), minute=cutoff.get("minute"), second=0
            )
        if date <= utc_cutoff_datetime or keep_same_day:
            # Postpone delivery to today's cutoff
            new_date = utc_cutoff_datetime
        else:
            # Postpone delivery to tomorrow's cutoff
            new_date = utc_cutoff_datetime + timedelta(days=1)
        return new_date
