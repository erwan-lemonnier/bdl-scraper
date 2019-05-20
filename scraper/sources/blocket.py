import logging
from scraper.scraper import GenericScraper


log = logging.getLogger(__name__)


class BlocketScraper(GenericScraper):

    def __init__(self, consumer):
        self.consumer = consumer

    def scan(self):
        pass


    def parse(self):
        pass
