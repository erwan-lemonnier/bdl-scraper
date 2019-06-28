#!/usr/bin/env python3
import os
import sys
import json
import logging
import requests
import click
from pymacaron.config import get_config
from pymacaron.auth import generate_token
from pymacaron.utils import timenow, to_epoch


log = logging.getLogger(__name__)


log.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
# formatter = logging.Formatter('%(message)s')
# handler.setFormatter(formatter)
log.addHandler(handler)
logging.getLogger('urllib3.connectionpool').setLevel(logging.INFO)


PATH_LIBS = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..')
sys.path.append(PATH_LIBS)

config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'pym-config.yaml')
get_config(config_path)


@click.command()
@click.option('--source', required=True, metavar='SOURCE', help="Scrape or scan this source (tradera, blocket, etc)")
@click.option('--scan/--no-scan', required=False, metavar='', help="Do a scan", default=False)
@click.option('--scrape', required=False, metavar='URL', help="Or scrape this url", default=None)
@click.option('--host', required=False, metavar='HOST', help="Call this host instead of scraper.bazardelux.com", default='crawler.bazardelux.com')
@click.option('--port', required=False, metavar='PORT', help="Call this port instead of 443", default='443')
@click.option('--async/--no-async', required=False, metavar='', help="Make the call asynchronous (otherwise wait and show result)", default=False)
@click.option('--limit-count', required=False, metavar='N', help="If scan, retrieve only the last N items", default=None)
@click.option('--back-secs', required=False, metavar='N', help="If scan, retrieve only items at most N seconds old", default=300)
def main(source, scan, scrape, host, port, async, limit_count, back_secs):
    """Scan or scrape a website using BDL's scrapers, either on api.bazardelux.com
    or locally.

    Examples:

    # Scan tradera for the last 10 new items\n
    python bin/scrape_source.py --scan --async --limit-count 10 --source tradera

    # Same, against the local server process\n
    python bin/scrape_source.py --host 127.0.0.1 --port 8080 --scan --async --limit-count 10 --source tradera

    # Test various error types in the TEST scraper
    python bin/scrape_source.py --source test --scrape assert
    python bin/scrape_source.py --source test --scrape crash
    python bin/scrape_source.py --source test --scrape error

    """

    log.debug("host = %s  | port = %s (type: %s)" % (host, port, type(port)))

    if not scan and not scrape:
        print("ERROR: One of --scan or --scrape must be chosen.")
        sys.exit(1)

    endpoint_url = '%s://%s:%s/v1/crawler/%s' % (
        'https' if port == '443' else 'http',
        host,
        port,
        'scan' if scan else 'scrape',
    )

    data = {}
    data['source'] = source.upper()
    if not async:
        data['synchronous'] = True
    if scrape:
        data['native_url'] = scrape
    if scan:
        data['epoch_oldest'] = int(to_epoch(timenow()) - back_secs)
        if limit_count:
            data['limit_count'] = int(limit_count)

    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer %s' % generate_token('scrape_source.py', data={}, expire_in=86400)
    }

    log.info("=> Calling POST %s: %s" % (endpoint_url, json.dumps(data, indent=4)))

    r = requests.post(endpoint_url, data=json.dumps(data), headers=headers)
    j = r.json()
    log.info("=> Got: %s" % json.dumps(j, indent=4))


if __name__ == "__main__":
    main()
