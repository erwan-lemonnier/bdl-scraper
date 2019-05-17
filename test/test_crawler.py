import logging
from unittest import TestCase
from scraper.crawler import GenericCrawler
from scraper.consumer import ItemConsumer


log = logging.getLogger(__name__)


class Tests(TestCase):

    def setUp(self):
        self.maxDiff = None

    def test_html_to_text(self):
        c = GenericCrawler(source='test', consumer=ItemConsumer(source='test'))
        tests = [
            # html, text
            ["", ""],
            ["bob<br>bob", "bob\nbob"],
            ["bob<bR/>bob", "bob\nbob"],
        ]

        for html, text in tests:
            self.assertEqual(c.html_to_text(html), text, "Converting '%s'" % html)


    def test_find_number(self):
        c = GenericCrawler(source='test', consumer=ItemConsumer(source='test'))
        tests = [
            # html, number
            ["<strong>Objektsnr:</strong>\n 351090548 \n", 351090548],
            ["**Objektsnr:**\n 351090548 \n", 351090548],
            ["**Objektsnr:**\n 35  109\n0548 \n", 351090548],
            ["409 kr", 409],
            ["5 909 kr", 5909],
        ]

        for html, n in tests:
            self.assertEqual(c.find_number(html), n, "Converting '%s'" % html)
