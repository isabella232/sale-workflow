# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from datetime import timedelta

from odoo import models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _get_workload(self, customer_lead):
        return 1 + customer_lead - self.company_id.security_lead

    def _expected_date(self):
        # Computes the expected date with respect to the WH calendar, if any.
        expected_date = super()._expected_date()
        return self._sale_warehouse_calendar_expected_date(expected_date)

    def _sale_warehouse_calendar_expected_date(self, expected_date):
        calendar = self.order_id.warehouse_id.calendar_id
        if calendar:
            customer_lead = self.customer_lead or 0.0
            td_customer_lead = timedelta(days=customer_lead)
            # remove customer lead added to order_date in sale_stock
            expected_date -= td_customer_lead
            workload = self._get_workload(customer_lead)
            # compute date given date_order and the actual workload
            expected_date = calendar.plan_days(workload, expected_date)
            # add back the customer lead time
            expected_date += td_customer_lead
        return expected_date

    def _prepare_procurement_values(self, group_id=False):
        res = super()._prepare_procurement_values(group_id=group_id)
        return self._sale_warehouse_calendar_prepare_procurement_values(res)

    def _sale_warehouse_calendar_prepare_procurement_values(self, res):
        date_planned = res.get("date_planned")
        calendar = self.order_id.warehouse_id.calendar_id
        if date_planned and calendar:
            customer_lead = self.customer_lead or 0.0
            workload = self._get_workload(customer_lead)
            res["date_planned"] = calendar.plan_days(workload, date_planned)
        return res
