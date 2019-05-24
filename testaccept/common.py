import logging
import os
from pymacaron.test import PyMacaronTestCase
from pymacaron.auth import generate_token


log = logging.getLogger(__name__)


class ScraperTests(PyMacaronTestCase):

    def setUp(self):
        super().setUp()
        self.maxDiff = None
        self.token = generate_token(
            'bdl-scraper-test',
            data={},
            # Expire in 3 days
            expire_in=259200,
        )


    def tearDown(self):
        super().tearDown()


    def assertIsCompleteTraderaItem(self, j):
        self.assertEqual(j['is_complete'], True)
        self.assertTrue(j['native_url'].startswith('https://www.tradera.com/item/'))
        j = j['bdlitem']
        self.assertTrue(j['native_picture_url'].startswith('https://img.tradera.net/images/'))
        self.assertTrue(j['epoch_published'] > 1558000000)
        self.assertTrue(type(j['native_doc_id']) is str)
        self.assertTrue(type(j['price']) is int)
        self.assertEqual(j['currency'], 'SEK')
        self.assertTrue(j['title'])
        self.assertTrue(type(j['description']) is str)
        self.assertEqual(j['is_sold'], False)
        self.assertTrue(j['native_seller_is_shop'] in (True, False))
        self.assertTrue(type(j['native_seller_name']) is str)
        self.assertTrue(j['price_is_fixed'] in (True, False))
        self.assertEqual(j['country'], 'SE')


    def assertIsIncompleteTraderaItem(self, j):
        self.assertEqual(j['is_complete'], False)
        self.assertTrue(j['native_url'].startswith('https://www.tradera.com/item/'))
        j = j['bdlitem']
        keys = list(j.keys())
        # native_picture_url is sometimes set. not always
        if 'native_picture_url' not in keys:
            keys.append('native_picture_url')
        self.assertEqual(set(keys), set(['price', 'currency', 'is_sold', 'title', 'native_picture_url', 'country']))
        self.assertEqual(j['is_sold'], False)
        self.assertTrue(type(j['price']) is int)
        self.assertEqual(j['country'], 'SE')


    def load_html(self, name):
        path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data/%s" % name)
        with open(path, 'r') as f:
            return f.read()
