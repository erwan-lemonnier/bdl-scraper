import logging
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
        self.assertTrue(j['epoch_published'] > 1558000000)
        self.assertTrue(type(j['native_doc_id']) is int)
        self.assertTrue(type(j['price']) is int)
        self.assertEqual(j['currency'], 'SEK')


    def assertIsIncompleteTraderaItem(self, j):
        self.assertEqual(j['is_complete'], False)
        self.assertTrue(j['native_url'].startswith('https://www.tradera.com/item/'))
        j = j['bdlitem']
        keys = list(j.keys())
        # native_picture_url is sometimes set. not always
        if 'native_picture_url' not in keys:
            keys.append('native_picture_url')
        self.assertEqual(set(keys), set(['price', 'currency', 'is_sold', 'title', 'native_picture_url']))
