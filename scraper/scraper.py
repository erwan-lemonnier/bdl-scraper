import logging
import re
import subprocess
from time import sleep
from html.parser import HTMLParser
from html2text import html2text
import requests.exceptions
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
import chromedriver_install as cdi
from selenium.webdriver.support.ui import WebDriverWait
from pymacaron.config import get_config
from scraper.consumer import ItemConsumer
from scraper.exceptions import ConsumerLimitReachedError
from scraper.exceptions import ConsumerEpochReachedError


log = logging.getLogger(__name__)


htmlparser = HTMLParser()


# Install chromedriver if needed and return its path
WEBDRIVER_PATH = cdi.install(file_directory='./lib/', verbose=True, chmod=True, overwrite=False, version=None)

CHROME_OPTIONS = webdriver.ChromeOptions()
CHROME_OPTIONS.add_argument('--no-sandbox')
CHROME_OPTIONS.add_argument('--window-size=1420,1080')
CHROME_OPTIONS.add_argument('--headless')
CHROME_OPTIONS.add_argument('--disable-gpu')
CHROME_OPTIONS.add_arguments('--disable-dev-shm-usage')
CHROME_OPTIONS.add_arguments('disable-infobars')
CHROME_OPTIONS.add_arguments('--disable-extensions')

# Test if chrome can be started
has_webdriver = False
try:
    d = webdriver.Chrome(
        executable_path=WEBDRIVER_PATH,
        options=CHROME_OPTIONS,
    )
    d.close()
    has_webdriver = True
except Exception as e:
    log.info("Chrome does not seem to be installed: %s" % str(e))
    log.info("Will use browserless.io instead.")
else:
    log.info("Chrome and webdriver are installed!")


def get_crawler(source, pre_loaded_html=None, **args):
    """Get a crawler for that source, properly initialized"""

    from scraper.sources.tradera import TraderaScraper
    from scraper.sources.blocket import BlocketScraper

    crawler_classes = {
        # source: crawler class
        'TRADERA': TraderaScraper,
        'BLOCKET': BlocketScraper,
    }

    if source not in crawler_classes:
        raise Exception("Don't know how to process objects from source %s" % source)

    return crawler_classes.get(source)(
        source=source,
        pre_loaded_html=pre_loaded_html,
        consumer=ItemConsumer(source, **args),
    )


class GenericScraper():
    """Empty interface that all scrapers must implement"""

    def __init__(self, source=None, consumer=None, pre_loaded_html=None):
        assert source, "source must be set"
        assert consumer, "consumer must be set"
        self.source = source
        self.consumer = consumer
        self.retry_delay = 1

        global has_webdriver
        self.driver = None
        if has_webdriver:
            options = webdriver.ChromeOptions()
            options.add_argument('headless')
            self.driver = webdriver.Chrome(
                executable_path=WEBDRIVER_PATH,
                options=CHROME_OPTIONS,
            )
            self.driver.implicitly_wait(10)
        # The soup
        self.soup = None
        self.html = None

        # Pre-load html, if available
        self.pre_loaded_html = pre_loaded_html


    def __del__(self):
        if self.driver:
            self.driver.close()


    def scan(self):
        raise Exception("Not implemented")


    def scrape(self, url, scraper_data=None):
        raise Exception("Not implemented")


    def scan_and_flush(self):
        """Call self.scan() within try loops that catch consumer limit errors"""
        try:
            self.scan()
        except ConsumerLimitReachedError as e:
            log.info(str(e))
        except ConsumerEpochReachedError as e:
            log.info(str(e))
        self.consumer.flush()


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

                if self.driver:
                    try:
                        log.info("Trying to fetch url %s" % url)
                        # TODO: Use webdriver/selenium to fetch url
                        self.driver.get(url)
                        if wait_condition:
                            WebDriverWait(self.driver, 10).until(wait_condition)
                        self.html = self.driver.page_source
                    except requests.exceptions.ConnectionError as e:
                        if retry:
                            log.warn("Got a ConnectionError. Sleeping %ssec and retrying..." % self.retry_delay)
                            sleep(self.retry_delay)
                        else:
                            raise e

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
