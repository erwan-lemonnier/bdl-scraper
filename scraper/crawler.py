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


log = logging.getLogger(__name__)


htmlparser = HTMLParser()


# TODO: implement proper check to know if chrome/webdriver is available
has_webdriver = False


class GenericCrawler():
    """Empty interface that all crawlers must implement"""

    def __init__(self, source=None, consumer=None):
        assert source, "source must be set"
        assert consumer, "consumer must be set"
        self.source = source
        self.consumer = consumer
        self.retry_delay = 3
        global has_webdriver
        if has_webdriver:
            self.driver = webdriver.Chrome()
            self.driver.implicitly_wait(30)
        # The soup
        self.soup = None


    def scan(self):
        raise Exception("Not implemented")


    def scrape(self, url, scraper_data=None):
        raise Exception("Not implemented")


    def safe_scan(self):
        """Call self.scan() within try loops that catch consumer limit errors"""
        try:
            self.scan()
        except ConsumerLimitReachedError:
            log.info("Consumer limit reached")


    def get_url(self, url):
        """Fetch a url. Retry up to 3 times"""
        log.debug("=> GET URL %s" % url)
        retry = 4
        while retry:
            retry = retry - 1
            sleep(1)

            if not has_webdriver:
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
                s = b.decode('utf-8')

                log.debug("Browserless replies: %s" % s[0:100])
                if '502 Bad Gateway' in s:
                    log.debug("Bad gateway, duh. Sleep 1sec and retry")
                    pass
                else:
                    # log.debug("Browserless replies: %s" % s)
                    self.soup = BeautifulSoup(s, 'lxml')
                    return True

            else:
                try:
                    log.info("Trying to fetch url %s" % url)
                    # TODO: Use webdriver/selenium to fetch url
                    self.driver.get_url()
                    self.soup = BeautifulSoup(self.driver.page_source, 'lxml')
                    return True
                except requests.exceptions.ConnectionError as e:
                    if retry:
                        log.warn("Got a ConnectionError. Sleeping %ssec and retrying..." % self.retry_delay)
                        sleep(self.retry_delay)
                    else:
                        raise e
        return False


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
