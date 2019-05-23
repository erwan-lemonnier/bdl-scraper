import logging
from unittest import TestCase
from scraper.scraper import GenericScraper
from scraper.consumer import ItemConsumer


log = logging.getLogger(__name__)


class Tests(TestCase):

    def setUp(self):
        self.maxDiff = None

    def test_html_to_text(self):
        c = GenericScraper(source='test', consumer=ItemConsumer(source='test'))
        tests = [
            # html, text
            ["", ""],
            ["bob<br>bob", "bob\nbob"],
            ["bob<bR/>bob", "bob\nbob"],
        ]

        for html, text in tests:
            self.assertEqual(c.html_to_text(html), text, "Converting '%s'" % html)


    def test_find_number(self):
        c = GenericScraper(source='test', consumer=ItemConsumer(source='test'))
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


    def test_date_to_epoch(self):
        c = GenericScraper(source='test', consumer=ItemConsumer(source='test'))
        tests = [
            # date, gmt, epoch
            ['23 May 2019 20:57:00', None, 1558637820],
            ['23 May 2019 20:57:00', 'Europe/Stockholm', 1558637820],
            ['2019-05-23 20:57', None, 1558637820],
            ['Thu May 23 22:02:14', None, 1558641734],
        ]

        for date, tzname, epoch in tests:
            self.assertEqual(c.date_to_epoch(date, tzname=tzname), epoch, "Converting '%s'" % date)
