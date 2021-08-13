# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from datetime import timedelta

from odoo import models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _expected_date(self):
        # Computes the expected date with respect to the WH calendar, if any.
        res = super()._expected_date()
        calendar = self.order_id.warehouse_id.calendar_id
        if calendar:
            customer_lead = self.customer_lead or 0.0
            td_customer_lead = timedelta(days=customer_lead)
            # remove customer lead added to order_date in sale_stock
            res -= td_customer_lead
            workload = 1 + customer_lead + self.company_id.security_lead
            # compute date given date_order and the actual workload
            res = calendar.with_context(debug_tests=True).plan_days(workload, res)
            # add back the customer lead time
            res += td_customer_lead
        return res

    def _prepare_procurement_values(self, group_id=False):
        res = super()._prepare_procurement_values()
        calendar = self.order_id.warehouse_id.calendar_id
        if calendar:
            date_planned = res.get("date_planned")
            if date_planned:
                customer_lead = self.customer_lead or 0.0
                workload = 1 + customer_lead - self.company_id.security_lead
                res["date_planned"] = calendar.plan_days(workload, date_planned)
        return res
