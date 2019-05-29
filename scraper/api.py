import logging
from pymacaron_core.swagger.apipool import ApiPool
from pymacaron.utils import to_epoch, timenow
from pymacaron_async import asynctask
from scraper.scraper import get_crawler


log = logging.getLogger(__name__)


def empty_response(source, **whatever):
    return ApiPool.scraper.model.ScrapedObjects(
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
        scraper = scan(source, allow_flush=False, **settings)
        return scraper.consumer.get_scraped_objects()

    # Execute asynchronously
    async_scan(source, **settings)
    return empty_response(source, **settings)


@asynctask()
def async_scan(*args, **kwargs):
    scan(*args, **kwargs)


def scan(source, **kwargs):
    c = get_crawler(source, **kwargs)
    c.scan_and_flush()
    return c


#
# SCRAPE
#

def do_scrape_source(data):
    source = data.source.upper()
    if data.synchronous not in (False, True):
        data.synchronous = True

    settings = {
        'pre_loaded_html': data.html if data.html else None,
        'native_url': data.native_url,
        'scraper_data': data.scraper_data,
    }

    if data.synchronous:
        scraper = scrape(source, **settings)
        return scraper.consumer.get_scraped_objects()

    async_scrape(source, **settings)
    return empty_response(source, **settings)


def scrape(source, pre_loaded_html=None, native_url=None, scraper_data=None):
    c = get_crawler(source, pre_loaded_html=pre_loaded_html)
    c.scrape(
        native_url,
        scraper_data,
    )
    return c


@asynctask()
def async_scrape(*args, **kwargs):
    scrape(*args, **kwargs)
