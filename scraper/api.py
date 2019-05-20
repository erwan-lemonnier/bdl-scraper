import logging
from pymacaron_core.swagger.apipool import ApiPool
from pymacaron.utils import to_epoch, timenow
from pymacaron_async import asynctask
from scraper.scraper import get_crawler


log = logging.getLogger(__name__)


def scan(source, **args):
    c = get_crawler(source, **args)
    c.scan_and_flush()
    return c


@asynctask
def async_safe_scan(source, **args):
    scan(source, **args)


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

    if data.synchronous:
        crawler = scan(source, allow_flush=False, **settings)
        return crawler.consumer.get_scraped_objects()

    # Execute asynchronously
    async_safe_scan(source, **settings)
    return ApiPool.scraper.model.ScrapedObjects(
        epoch_youngest=data.epoch_youngest,
        epoch_oldest=data.epoch_oldest,
    )



def do_scrape_source(data):
    source = data.source.upper()
    c = get_crawler(source, pre_loaded_html=data.html)
    return c.scrape(
        data.native_url,
        data.scraper_data,
    )
