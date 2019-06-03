import logging
from pymacaron_core.swagger.apipool import ApiPool
from pymacaron.utils import to_epoch, timenow
from pymacaron_async import asynctask
from crawler.crawler import get_crawler
from crawler.exceptions import ConsumerLimitReachedError
from crawler.exceptions import ConsumerEpochReachedError
from crawler.exceptions import InternalServerError


log = logging.getLogger(__name__)


def empty_response(source, **whatever):
    return ApiPool.crawler.model.ScrapedObjects(
        index='BDL',
        source=source.upper(),
        real=True,
        objects=[],
    )


#
# SCAN
#

def do_scan_source(data):

    source = data.source.upper()
    now = to_epoch(timenow())
    if data.synchronous not in (False, True):
        data.synchronous = False

    settings = {
        'epoch_youngest': data.epoch_youngest if data.epoch_youngest else now,
        'epoch_oldest': data.epoch_oldest if data.epoch_oldest else now - 86400,
        'limit_sec': data.limit_sec if data.limit_sec else None,
        'limit_count': data.limit_count if data.limit_count else None,
        'pre_loaded_html': data.html,
    }

    log.debug("Scan settings are: %s" % settings)
    if data.synchronous:
        crawler = scan(source, allow_flush=False, **settings)
        return crawler.consumer.get_scraped_objects()

    # Execute asynchronously
    async_scan(source, **settings)
    return empty_response(source, **settings)


@asynctask()
def async_scan(*args, **kwargs):
    scan(*args, **kwargs)


def scan(source, **kwargs):
    c = get_crawler(source, **kwargs)

    # Scan and catch limit reached exceptions
    try:
        c.scan()
    except ConsumerLimitReachedError as e:
        log.info(str(e))
    except ConsumerEpochReachedError as e:
        log.info(str(e))

    # Empty the buffer of scraped objects
    c.consumer.flush()

    return c


#
# SCRAPE
#

def do_scrape_source(data):
    source = data.source.upper()
    if data.synchronous not in (False, True):
        data.synchronous = False

    settings = {
        'pre_loaded_html': data.html if data.html else None,
        'native_url': data.native_url,
        'scraper_data': data.scraper_data,
    }

    if data.synchronous:
        crawler = scrape(source, allow_flush=False, **settings)
        return crawler.consumer.get_scraped_objects()

    async_scrape(source, **settings)
    return empty_response(source, **settings)


@asynctask()
def async_scrape(*args, **kwargs):
    scrape(*args, **kwargs)


def scrape(source, pre_loaded_html=None, native_url=None, scraper_data=None, allow_flush=True):
    c = get_crawler(source, pre_loaded_html=pre_loaded_html, allow_flush=allow_flush)
    c.scrape(
        native_url,
        scraper_data,
    )
    c.consumer.flush()
    return c


#
# SEARCH
#

def do_search_source(data):
    source = data.source.upper()
    if data.synchronous in (False, None):
        raise InternalServerError("Asynchronous mode is not supported for search")

    c = get_crawler(source, allow_flush=False)
    c.search(data.query)

    return c.consumer.get_scraped_objects()
