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
from pymacaron.config import get_config
from scraper.exceptions import ConsumerLimitReachedError
from scraper.exceptions import ConsumerEpochReachedError


log = logging.getLogger(__name__)


htmlparser = HTMLParser()


# TODO: implement proper check to know if chrome/webdriver is available
has_webdriver = False


class GenericCrawler():
    """Empty interface that all crawlers must implement"""

    def __init__(self, source=None, consumer=None, pre_loaded_html=None):
        assert source, "source must be set"
        assert consumer, "consumer must be set"
        self.source = source
        self.consumer = consumer
        self.retry_delay = 1

        global has_webdriver
        if has_webdriver:
            self.driver = webdriver.Chrome()
            self.driver.implicitly_wait(30)
        # The soup
        self.soup = None
        self.html = None

        # Pre-load html, if available
        self.pre_loaded_html = pre_loaded_html


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


    def get_url(self, url):
        """Fetch a url. Retry up to 3 times"""

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

                if has_webdriver:
                    try:
                        log.info("Trying to fetch url %s" % url)
                        # TODO: Use webdriver/selenium to fetch url
                        self.driver.get_url()
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
