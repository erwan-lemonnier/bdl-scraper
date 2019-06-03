import logging
from pymacaron.utils import to_epoch, timenow
from pymacaron.exceptions import is_error
from pymacaron_core.swagger.apipool import ApiPool
from crawler.exceptions import ConsumerLimitReachedError
from crawler.exceptions import ConsumerEpochReachedError
from crawler.exceptions import ApiCallError
from crawler.io.slack import slack_info

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

        # Allow flushing/emptying buffer or not
        self.allow_flush = allow_flush

        # Auto-flush once the processed items buffer reached that many items
        self.flush_count = 50

        log.info("Initialized consumer: allow_flush=%s limit_sec=%s limit_count=%s" % (allow_flush, limit_sec, limit_count))
        log.info("Initialized consumer: epoch_oldest=%s epoch_youngest=%s" % (epoch_oldest, epoch_youngest))


    def process(self, object):
        """Swallow a scraped object and return True if the crawler should proceed
        scraping and sending the next object, or False if the crawler should
        stop.

        """

        if self.limit_sec and to_epoch(timenow()) - self.time_start > self.limit_sec:
            raise ConsumerLimitReachedError("The time limit of %s sec has passed - Stopping now." % self.limit_sec)

        if self.epoch_oldest and hasattr(object, 'bdlitem') and object.bdlitem and object.bdlitem.epoch_published:
            if object.bdlitem.epoch_published < self.epoch_oldest:
                raise ConsumerEpochReachedError("Parsed an item whose epoch_oldest %s is older than the limit %s" % (object.bdlitem.epoch_published, self.epoch_oldest))

        self.objects.append(object)
        self.count_items = self.count_items + 1
        log.info("Scanned %s objects so far (Count limit is %s)" % (self.count_items, self.limit_count))

        # Do we keep processing?
        if self.limit_count and self.count_items >= self.limit_count:
            raise ConsumerLimitReachedError("The limit count of %s items have been fetched - Stopping now." % self.limit_count)

        # Do we flush?
        if self.allow_flush and len(self.objects) > self.flush_count:
            log.info("Reached %s items - Calling flush" % len(self.objects))
            self.flush()

        return object


    def flush(self):
        """If allow_flush is on, send all scanned objects so far to the BDL api and reset
        the list of scanned objects.

        """

        if not self.allow_flush:
            log.info("Flush: allow_flush=False - Not sending objects to BDL api")
            return

        log.debug("Flush: sending %s scanned objects to BDL api" % len(self.objects))

        data = ApiPool.bdl.model.ScrapedObjects(
            index='BDL',
            source=self.source.upper(),
            real=True,
            objects=[
                ApiPool.bdl.json_to_model(
                    'ScrapedObject',
                    ApiPool.crawler.model_to_json(o),
                ) for o in self.objects
            ],
        )

        # And send the scraped objects to the BDL api
        r = ApiPool.bdl.client.process_items(data)
        if is_error(r):
            raise ApiCallError("Flush error: %s" % r.error_description)

        slack_info(
            self.source,
            "Flushed %s items %s" % (
                len(self.objects),
                '' if len(self.objects) == 0 else '(1st one: %s | %s)' % (
                    self.objects[0].native_url,
                    'complete' if self.objects[0].is_complete else 'incomplete',
                ),
            )
        )

        # And empty the buffer
        self.objects = []


    def get_scraped_objects(self):
        """Return a ScrapedObjects containing all scraped objects"""

        return ApiPool.crawler.model.ScrapedObjects(
            index='BDL',
            source=self.source.upper(),
            real=True,
            objects=self.objects if self.objects else [],
        )
