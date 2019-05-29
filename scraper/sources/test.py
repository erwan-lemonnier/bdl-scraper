import logging
from scraper.scraper import GenericScraper


log = logging.getLogger(__name__)


class TestScraper(GenericScraper):


    def scrape(self, native_url, scraper_data=None):
        """Simulate scraping a url"""

        log.info("TEST: mock scraping url %s" % native_url)

        return None


    def scan(self):
        """Simulate scanning source"""

        log.info("TEST: mock scanning source TEST")

        return None
