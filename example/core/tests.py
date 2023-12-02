import logging

from django.test import TestCase
from core.models import UserAction


logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)


class Test(TestCase):
    databases = ["default", "db_cold"]

    def test_all(self):
        hot_data = UserAction(type="hot")
        hot_data.save(using="default")
        cold_data = UserAction(type="cold")
        cold_data.save(using="db_cold")
        data = list(UserAction.objects.all())
        self.assertEqual(
                UserAction.objects.count(),
                2,
        )
        self.assertEqual(
                len(data), 
                2,
        )
        cold_data = list(UserAction.objects.filter(type="cold"))
        self.assertEqual(
                len(cold_data), 
                1,
        )

    def test_order(self):
        data1 = UserAction(id=1, type="type4")
        data1.save(using="default")
        data2 = UserAction(id=2, type="type3")
        data2.save(using="db_cold")
        data3 = UserAction(id=3, type="type1")
        data3.save(using="db_cold")
        data4 = UserAction(id=4, type="type2")
        data4.save(using="default")
        order_qs = UserAction.objects.order_by(
            "type", "pk")
        data = list(order_qs)
        LOGGER.info(data)
        self.assertEqual(data[0].type, "type1")
        self.assertEqual(data[1].type, "type2")
        self.assertEqual(data[2].type, "type3")
        self.assertEqual(data[3].type, "type4")