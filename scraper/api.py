import logging
from pymacaron_core.swagger.apipool import ApiPool
from pymacaron.utils import to_epoch, timenow
from pymacaron_async import asynctask
from scraper.consumer import get_crawler


log = logging.getLogger(__name__)


@asynctask
def async_safe_scan(source, data):
    c = get_crawler(source, **ApiPool.scraper.model_to_json(data))
    c.scan_and_flush()


def do_scan_source(source, data):

    source = source.lower()
    now = to_epoch(timenow())

    if not data.epoch_youngest:
        data.epoch_youngest = now
    if not data.epoch_oldest:
        data.epoch_oldest = now - 86400

    async_safe_scan(source, data)

    return ApiPool.scraper.model.ScanInterval(
        epoch_youngest=data.epoch_youngest,
        epoch_oldest=data.epoch_oldest,
    )


def do_scrape_source(source, data):
    source = source.lower()
    c = get_crawler(source)
    return c.scrape(
        data.native_url,
        data.scraper_data,
    )
