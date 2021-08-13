# Copyright Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from datetime import datetime

from freezegun import freeze_time

from odoo.tests.common import SavepointCase

WORKING_DAYS = list(range(5))  # working days are from monday to friday included
CUTOFF_TIME = 8.0  # cutoff time will be set at 8 a.m.


class TestSaleOrderDates(SavepointCase):
    at_install = False
    post_install = True

    @classmethod
    def _define_calendar(cls, name, attendances):
        return cls.env["resource.calendar"].create(
            {
                "name": name,
                "attendance_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "%s_%d" % (name, index),
                            "hour_from": att[0],
                            "hour_to": att[1],
                            "dayofweek": str(att[2]),
                        },
                    )
                    for index, att in enumerate(attendances)
                ],
            }
        )

    @classmethod
    def setupClassCompany(cls):
        cls.company = cls.env.user.company_id
        cls.company.security_lead = 1

    @classmethod
    def setUpClassCalendar(cls):
        cls.calendar = cls._define_calendar("40 Hours", [(8, 16, i) for i in range(5)],)

    @classmethod
    def setUpClassWarehouse(cls):
        cls.warehouse = cls.env.ref("stock.warehouse0")
        cls.warehouse.write(
            {
                "cutoff_time": CUTOFF_TIME,
                "apply_cutoff": True,
                "calendar_id": cls.calendar,
            }
        )

    @classmethod
    def setUpClassPartner(cls):
        cls.customer = cls.env.ref("base.res_partner_12")
        cls.customer.order_delivery_cutoff_preference = "warehouse_cutoff"
        cls.customer.delivery_time_preference = "workdays"

    @classmethod
    def setUpClassProduct(cls):
        cls.product = cls.env.ref("product.product_product_3")

    @classmethod
    def setUpClass(cls):
        super(TestSaleOrderDates, cls).setUpClass()
        cls.env = cls.env(
            context=dict(cls.env.context, tracking_disable=True, tz="UTC")
        )
        cls.setupClassCompany()
        cls.setUpClassCalendar()
        cls.setUpClassWarehouse()
        cls.setUpClassPartner()
        cls.setUpClassProduct()

    def _create_order(self, dt):
        with freeze_time(dt.strftime("%Y-%m-%d %H:%M:%S")):
            order = self.env["sale.order"].create(
                {"partner_id": self.customer.id, "warehouse_id": self.warehouse.id}
            )
            self.env["sale.order.line"].create(
                {
                    "order_id": order.id,
                    "product_id": self.product.id,
                    "product_uom_qty": 1,
                    "customer_lead": 1,
                }
            )
            return order

    @freeze_time("2021-08-13 07:00:00")
    def test_confirm_before_cutoff_last_weekday(self):
        order = self._create_order(datetime.now())
        order.action_confirm()
        self.assertEqual(order.expected_date, datetime(2021, 8, 18, 16, 0, 0))

    @freeze_time("2021-08-13 09:00:00")
    def test_confirm_after_cutoff_last_weekday(self):
        # - expected delivery date thursday the 19th
        # - customer lead time is 1 day
        # - company security lead is 1 day
        # - cutoff < now -> today isn't included
        # - date order = today
        # working days next monday, next tuesday, next wednesday
        order = self._create_order(datetime.now())
        order.action_confirm()
        self.assertEqual(order.expected_date, datetime(2021, 8, 19, 16, 0, 0))
