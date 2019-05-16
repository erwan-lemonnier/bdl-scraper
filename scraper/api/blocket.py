import logging
from scraper.crawler import GenericCrawler


log = logging.getLogger(__name__)


class BlocketCrawler(GenericCrawler):

    def __init__(self, consumer):
        self.consumer = consumer

    def scan(self):
        pass


    def parse(self):
        pass
