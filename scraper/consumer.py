import logging
from pymacaron.utils import to_epoch, timenow
from pymacaron_core.swagger.apipool import ApiPool
from scraper.exceptions import ConsumerLimitReachedError
from scraper.exceptions import ConsumerEpochReachedError


log = logging.getLogger(__name__)


class ItemConsumer():

    def __init__(self, source, epoch_youngest=None, epoch_oldest=None, limit_count=None, limit_sec=None, allow_flush=True):
        assert source
        self.source = source
        self.epoch_youngest = epoch_youngest
        self.epoch_oldest = epoch_oldest
        self.limit_count = limit_count
        self.limit_sec = limit_sec
        self.time_start = to_epoch(timenow())
        self.count_items = 0
        self.last_scraped_object = None
        self.objects = []
        self.allow_flush = allow_flush

        log.info("Initialized consumer: allow_flush=%s limit_sec=%s limit_count=%s" % (allow_flush, limit_sec, limit_count))
        log.info("Initialized consumer: epoch_oldest=%s epoch_youngest=%s" % (epoch_oldest, epoch_youngest))


    def process(self, object):
        """Swallow a scraped object and return True if the scraper should proceed
        scraping and sending the next object, or False if the scraper should
        stop.

        """

        if self.limit_sec and to_epoch(timenow()) - self.time_start > self.limit_sec:
            raise ConsumerLimitReachedError("The time limit of %s sec has passed - Stopping now." % self.limit_sec)

        if self.epoch_oldest and hasattr(object, 'bdlitem') and object.bdlitem and object.bdlitem.epoch_published:
            if object.bdlitem.epoch_published < self.epoch_oldest:
                raise ConsumerEpochReachedError("Parsed an item whose epoch_oldest %s is older than the limit %s" % (object.bdlitem.epoch_published, self.epoch_oldest))

        self.objects.append(object)
        self.count_items = self.count_items + 1
        log.info("Scanned %s objects so far (limit is %s)" % (self.count_items, self.limit_count))

        # Do we keep processing?
        if self.limit_count and self.count_items >= self.limit_count:
            raise ConsumerLimitReachedError("The limit count of %s items have been fetched - Stopping now." % self.limit_count)

        return object


    def flush(self):
        """If allow_flush is on, send all scanned objects so far to the BDL api and reset
        the list of scanned objects.

        """

        if not self.allow_flush:
            log.info("Flush: allow_flush=False - Not sending objects to BDL api")
            return

        log.debug("Flush: sending %s scanned objects to BDL api" % len(self.objects))

        # r = requests.post(
        #     'https://api.bazardelux.com/v1/'
        # )

        # And reset object queue
        self.objects = []


    def get_scraped_objects(self):
        """Return a ScrapedObjects containing all scraped objects"""

        return ApiPool.scraper.model.ScrapedObjects(
            epoch_youngest=self.epoch_youngest,
            epoch_oldest=self.epoch_oldest,
            source=self.source,
            real=True,
            objects=self.objects,
        )
