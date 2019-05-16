import logging
from pymacaron.utils import to_epoch, timenow
from scraper.api.tradera import TraderaCrawler
from scraper.api.blocket import BlocketCrawler


log = logging.getLogger(__name__)


def get_crawler(source, **args):
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


    def process_and_go_on(self, object):
        """Swallow a scraped object and return True if the scraper should proceed
        scraping and sending the next object, or False if the scraper should
        stop.

        """

        if self.source == 'tradera':
            return self._proceed_tradera(object)
        elif self.source == 'blocket':
            return self._proceed_blocket(object)
        else:
            raise Exception("Don't know how to process objects from source %s" % self.source)

        # Do we keep processing?
        self.count_items = self.count_items + 1

        if self.limit_count and self.count_items >= self.limit_count:
            log.info("The limit count of %s items have been fetched - Stopping now." % self.limit_count)
            return False

        if self.limit_sec and to_epoch(timenow()) - self.time_start > self.limit_sec:
            log.info("The time limit of %s sec has passed - Stopping now." % self.limit_sec)
            return False

        # TODO: match object against epoch_oldest

        return True


    def _process_tradera(self, object):
        pass


    def _process_blocket(self, object):
        pass
