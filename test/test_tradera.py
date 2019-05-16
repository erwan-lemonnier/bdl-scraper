import os
import logging
from pymacaron_core.swagger.apipool import ApiPool
from scraper.formats import get_custom_formats
from unittest import TestCase
from scraper.api.tradera import TraderaCrawler
from scraper.consumer import ItemConsumer


log = logging.getLogger(__name__)


class Tests(TestCase):

    def setUp(self):
        ApiPool.add(
            'scraper',
            yaml_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'apis', 'scraper.yaml'),
            formats=get_custom_formats(),
        )
        self.maxDiff = None


    def test_init(self):
        TraderaCrawler(source='tradera', consumer=ItemConsumer('tradera'))


    def test_scan_10_items(self):
        # Fetch the last 10 tradera announces and queue them up
        consumer = ItemConsumer('tradera', limit_count=10)
        c = TraderaCrawler(
            source='tradera',
            consumer=consumer,
        )

        c.scan()
        self.assertEqual(consumer.count_items, 10)
