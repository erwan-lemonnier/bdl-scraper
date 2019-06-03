import logging
from crawler.crawler import GenericCrawler
from crawler.exceptions import InternalServerError


log = logging.getLogger(__name__)


class TestCrawler(GenericCrawler):


    def scrape(self, native_url, scraper_data=None):
        """Simulate scraping a url"""

        log.info("TEST: mock scraping url %s" % native_url)

        if 'assert' in native_url:
            assert 0, "Test failing an assert"

        if 'crash' in native_url:
            int("bob")

        if 'error' in native_url:
            raise InternalServerError("Test raising fatal error")

        return None


    def scan(self):
        """Simulate scanning source"""

        log.info("TEST: mock scanning source TEST")

        return None
