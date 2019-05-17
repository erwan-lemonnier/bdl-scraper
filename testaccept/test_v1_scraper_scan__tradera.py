import os
import imp
import logging


common = imp.load_source('common', os.path.join(os.path.dirname(__file__), 'common.py'))


log = logging.getLogger(__name__)


class Tests(common.ScraperTests):

    def test_v1_tradera_scan__auth_required(self):
        self.assertPostReturnError(
            'v1/scraper/scan',
            {'source': 'TEST'},
            401,
            'AUTHORIZATION_HEADER_MISSING',
        )

    def test_v1_tradera_scan__10_items(self):
        j = self.assertPostReturnJson(
            'v1/scraper/scan',
            {
                'source': 'TRADERA',
                'limit_count': 10,
                'async': False,
            },
            auth='Bearer %s' % self.token,
        )

        objects = j['objects']
        self.assertEqual(len(objects), 10)

        j['objects'] = []
        self.assertEqual(
            j,
            {
                'epoch_youngest': j['epoch_youngest'],
                'epoch_oldest': j['epoch_oldest'],
                'source': 'TRADERA',
                'real': True,
                'objects': [],
            }
        )

        j = objects.pop(0)
        self.assertIsCompleteTraderaItem(j)

        for j in objects:
            self.assertIsIncompleteTraderaItem(j)
