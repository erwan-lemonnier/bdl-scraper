import logging
from pymacaron_core.swagger.apipool import ApiPool
from pymacaron.utils import to_epoch, timenow
from pymacaron_async import asynctask
from scraper.consumer import get_crawler


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

    settings = {
        'epoch_youngest': data.epoch_youngest if data.epoch_youngest else now,
        'epoch_oldest': data.epoch_oldest if data.epoch_oldest else now - 86400,
        'limit_sec': data.limit_sec if data.limit_sec else None,
        'limit_count': data.limit_count if data.limit_count else None,
    }

    if data.async:
        async_safe_scan(source, **settings)
        return ApiPool.scraper.model.ScrapedObjects(
            epoch_youngest=data.epoch_youngest,
            epoch_oldest=data.epoch_oldest,
        )

    crawler = scan(source, allow_flush=False, **settings)

    return crawler.consumer.get_scraped_objects()


def do_scrape_source(source, data):
    source = source.lower()
    c = get_crawler(source)
    return c.scrape(
        data.native_url,
        data.scraper_data,
    )
