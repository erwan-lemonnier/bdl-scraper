import logging
from pymacaron.utils import to_epoch, timenow
from scraper.exceptions import ConsumerLimitReachedError
from scraper.sources.tradera import TraderaCrawler
from scraper.sources.blocket import BlocketCrawler


log = logging.getLogger(__name__)


def get_crawler(source, epoch_youngest=None, epoch_oldest=None, limit_count=None, limit_sec=None):
    """Get a crawler for that source, properly initialized"""

    crawler_classes = {
        # source: crawler class
        'tradera': TraderaCrawler,
        'blocket': BlocketCrawler,
    }
    if source not in crawler_classes:
        raise Exception("Don't know how to process objects from source %s" % source)

    return crawler_classes.get(source)(
        source=source,
        consumer=ItemConsumer(source),
    )


class ItemConsumer():

    def __init__(self, source=None, epoch_youngest=None, epoch_oldest=None, limit_count=None, limit_sec=None):
        assert source
        self.source = source
        self.epoch_youngest = epoch_youngest
        self.epoch_oldest = epoch_oldest
        self.limit_count = limit_count
        self.limit_sec = limit_sec
        self.time_start = to_epoch(timenow())
        self.count_items = 0
        self.last_scraped_object = None


    def process(self, object):
        """Swallow a scraped object and return True if the scraper should proceed
        scraping and sending the next object, or False if the scraper should
        stop.

        """

        # Do we keep processing?
        if self.limit_count and self.count_items >= self.limit_count:
            raise ConsumerLimitReachedError("The limit count of %s items have been fetched - Stopping now." % self.limit_count)

        if self.limit_sec and to_epoch(timenow()) - self.time_start > self.limit_sec:
            raise ConsumerLimitReachedError("The time limit of %s sec has passed - Stopping now." % self.limit_sec)

        if self.epoch_oldest and object.epoch_oldest < self.epoch_oldest:
            raise ConsumerLimitReachedError("Parsed an item whose epoch_oldest %s is older than the limit %s" % (object.epoch_oldest, self.epoch_oldest))

        self.count_items = self.count_items + 1

        # TODO: And push object to the BDL API

        return object
