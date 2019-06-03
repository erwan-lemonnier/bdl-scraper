import os
import imp
import logging


common = imp.load_source('common', os.path.join(os.path.dirname(__file__), 'common.py'))


log = logging.getLogger(__name__)


class Tests(common.CrawlerTests):

    def test_v1_crawler_scan__test__synchronous(self):
        j = self.assertPostReturnJson(
            'v1/crawler/scan',
            {
                'source': 'TEST',
                'limit_count': 10,
                'synchronous': True,
            },
            auth='Bearer %s' % self.token,
        )

        self.assertEqual(
            j,
            {
                'source': 'TEST',
                'real': True,
                'index': 'BDL',
                'objects': [],
            }
        )


    def test_v1_crawler_scan__test__asynchronous(self):
        j = self.assertPostReturnJson(
            'v1/crawler/scan',
            {
                'source': 'TEST',
                'limit_count': 10,
            },
            auth='Bearer %s' % self.token,
        )

        self.assertEqual(
            j,
            {
                'source': 'TEST',
                'real': True,
                'index': 'BDL',
                'objects': [],
            }
        )


    def test_v1_crawler_scrape__test__synchronous(self):
        j = self.assertPostReturnJson(
            'v1/crawler/scrape',
            {
                'source': 'TEST',
                'native_url': 'doesnotmatter',
                'synchronous': True,
            },
            auth='Bearer %s' % self.token,
        )

        self.assertEqual(
            j,
            {
                'source': 'TEST',
                'real': True,
                'index': 'BDL',
                'objects': [],
            }
        )
