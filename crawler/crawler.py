import logging
import re
import os
import subprocess
from time import sleep
from html.parser import HTMLParser
from html2text import html2text
import requests.exceptions
import requests
from dateutil import parser
from datetime import datetime, timedelta, timezone
import pytz
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from pymacaron.config import get_config
from crawler.consumer import ItemConsumer
from crawler.exceptions import UnknownSourceError
from crawler.io.slack import slack_info


log = logging.getLogger(__name__)


htmlparser = HTMLParser()


# Try finding chromedriver if needed and return its path
HERE = os.path.dirname(os.path.realpath(__file__))
os.environ['PATH'] += ':%s/../lib/:/pym/lib' % HERE
log.info("Searching for chromedriver in PATH=%s" % os.environ['PATH'])
WEBDRIVER_PATH = os.popen('which chromedriver').read().strip()
log.info("Found chromedriver at %s" % WEBDRIVER_PATH)

CHROME_OPTIONS = webdriver.ChromeOptions()
CHROME_OPTIONS.add_argument('--no-sandbox')
CHROME_OPTIONS.add_argument('--window-size=1420,1080')
CHROME_OPTIONS.add_argument('--headless')
CHROME_OPTIONS.add_argument('--disable-gpu')
CHROME_OPTIONS.add_argument('--disable-dev-shm-usage')
CHROME_OPTIONS.add_argument('disable-infobars')
CHROME_OPTIONS.add_argument('--disable-extensions')


def get_crawler(source, pre_loaded_html=None, **args):
    """Get a crawler for that source, properly initialized"""

    from crawler.sources.tradera import TraderaCrawler
    from crawler.sources.blocket import BlocketCrawler
    from crawler.sources.test import TestCrawler

    crawler_classes = {
        # source: crawler class
        'TRADERA': TraderaCrawler,
        'BLOCKET': BlocketCrawler,
        'TEST': TestCrawler,
    }

    if source not in crawler_classes:
        raise UnknownSourceError("Don't know how to process objects from source %s" % source)

    return crawler_classes.get(source)(
        source=source,
        pre_loaded_html=pre_loaded_html,
        consumer=ItemConsumer(source, **args),
    )


class GenericCrawler():
    """Empty interface that all crawlers must implement"""

    def __init__(self, source=None, consumer=None, pre_loaded_html=None):
        assert source, "source must be set"
        assert consumer, "consumer must be set"
        self.source = source
        self.consumer = consumer
        self.retry_delay = 1

        self.has_webdriver = None

        # The soup
        self.soup = None
        self.html = None

        # Pre-load html, if available
        self.pre_loaded_html = pre_loaded_html


    def scan(self):
        raise Exception("Not implemented")


    def scrape(self, url, scraper_data=None):
        raise Exception("Not implemented")


    def get_webdriver(self):
        """Return webdriver if it is available on the host, else None"""

        if self.has_webdriver is False:
            return None
        elif WEBDRIVER_PATH == '':
            self.has_webdriver = False
            return None
        elif self.has_webdriver in (None, True):
            # Test if chrome can be started
            try:
                driver = webdriver.Chrome(
                    executable_path=WEBDRIVER_PATH,
                    options=CHROME_OPTIONS,
                )
                self.has_webdriver = True
                return driver
            except Exception as e:
                log.info("Chrome does not seem to be installed: %s" % str(e))
                log.info("Will use browserless.io instead.")
                self.has_webdriver = False
                return None


    def get_url(self, url, wait_condition=None):
        """Fetch a url. Retry up to 3 times. Optionally take a webdriver wait
        condition, as described at
        https://selenium-python.readthedocs.io/waits.html

        """

        self.html = None

        if self.pre_loaded_html:
            log.debug("Using pre-loaded html: %s.." % self.pre_loaded_html[0:50])
            self.html = self.pre_loaded_html
            self.pre_loaded_html = None
        else:
            log.debug("=> GET URL %s" % url)
            retry = 4
            while not self.html and retry:
                retry = retry - 1

                driver = self.get_webdriver()
                if driver:
                    try:
                        log.info("Trying to fetch url %s" % url)
                        # TODO: Use webdriver/selenium to fetch url
                        driver.get(url)
                        if wait_condition:
                            WebDriverWait(driver, 10).until(wait_condition)
                    except requests.exceptions.ConnectionError as e:
                        if retry:
                            log.warn("Got a ConnectionError. Sleeping %ssec and retrying..." % self.retry_delay)
                            sleep(self.retry_delay)
                        else:
                            driver.close()
                            raise e

                    self.html = driver.page_source
                    driver.close()

                else:
                    # Use browserless.io to fetch rendered pages

                    # Huh? requests does not work against browserless??
                    # r = requests.post(
                    #     'https://chrome.browserless.io/content?token=%s' % get_config().browserless_api_key,
                    #     data={
                    #         'url': 'https://example.com/',
                    #     },
                    # )

                    u = 'https://chrome.browserless.io/content?token=%s' % get_config().browserless_api_key
                    data = '{"url": "%s"}' % url
                    b = subprocess.check_output(['curl', '-X', 'POST', u, '-H', 'Cache-Control: no-cache', '-H', 'Content-Type: application/json', '-d', data])
                    html = b.decode('utf-8')

                    log.debug("Browserless replies: %s" % html[0:100])
                    if '502 Bad Gateway' in html:
                        if retry:
                            log.debug("Bad gateway, duh. Sleep %ssec and retry" % self.retry_delay)
                            sleep(self.retry_delay)
                        else:
                            raise Exception("Browserless: Bad gateway")
                    else:
                        self.html = html

        if not self.html:
            log.debug("Failed to get HTML from %s" % url)
            return False

        self.soup = BeautifulSoup(self.html, 'lxml')

        slack_info(
            self.source.upper(),
            "fetched %s" % url,
            channel=get_config().slack_urls,
        )

        return True


    def get_soup(self):
        """Return the beautifulsoup for the current page. None if no page loaded"""
        return self.soup


    def html_to_text(self, html):
        """Take some html text and return a text string, cleaned up of all html and normalized"""
        s = html2text(html)
        s = htmlparser.unescape(s)
        s = s.replace('\.', '.')
        s = s.replace('\*', '*')
        s = re.sub(re.compile('^[\s]+', re.MULTILINE), '', s)
        s = re.sub(re.compile('[\s]+$', re.MULTILINE), '', s)
        return s


    def find_number(self, html):
        s = self.html_to_text(html)
        s = re.sub(re.compile('[\r\n]+', re.MULTILINE), '', s)
        s = re.sub(r'^[^\d]*', '', s)
        s = re.sub(r'[^\d]*$', '', s)
        s = s.replace(' ', '')
        return int(s)


    def date_to_epoch(self, s, tzname=None):
        """Parse a date string without timezone, of the form YYYY-MM-DD HH:MM into an
        epoch, assuming Stockholm's timezone by default

        """

        # Convert first to a naive date
        date = parser.parse(s, ignoretz=True)

        # And add the timezone
        if not tzname:
            tz = pytz.timezone('Europe/Stockholm')
        else:
            tz = pytz.timezone(tzname)
        date = tz.localize(date)

        assert date.tzinfo

        t0 = datetime(1970, 1, 1, tzinfo=timezone.utc)
        delta = (date - t0) / timedelta(seconds=1)
        return int(delta)
