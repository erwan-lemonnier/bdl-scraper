import logging
from urllib.parse import urlencode
import json
from dateutil import parser
from pymacaron_core.swagger.apipool import ApiPool
from pymacaron.crash import report_error
from pymacaron.utils import to_epoch
from scraper.crawler import GenericCrawler
from scraper.exceptions import ParserError
from scraper.exceptions import CannotGetUrlError
from scraper.exceptions import SkipThisItem
from scraper.exceptions import ConsumerEpochReachedError


log = logging.getLogger(__name__)


COUNTRY = 'SE'
BASE_URL = 'https://www.tradera.com'

TRADERA_CATEGORIES = [
    'antikt-design-20',
    'accessoarer-1612',
    'inredningsdetaljer-c3_1609',
    'lampor-c3_302528',
    'mobler-c3_1604',
    'exklusiva-klockor-c3_1901',
    'modeklockor-c3_1904',
    'konst-23',
]

class TraderaCrawler(GenericCrawler):

    def __init__(self, **args):
        log.debug("TraderaCrawler got init args: %s" % args)
        super().__init__(**args)
        self.country = COUNTRY
        self.count_page = 0


    def scan(self):

        for category in TRADERA_CATEGORIES:

            page_next = self.gen_first_page_url(category)
            epoch_published = None

            try:
                while page_next:

                    # Fetch next listing page
                    self.get_url(page_next)

                    # Get the url of the next listing page to scrape
                    page_next = self.get_next_page_url()

                    # scrape the current listing page
                    for item in self.yield_listing_page_items():

                        # The listing page does not show the publication time
                        # of the announce, but we know that they are listed by
                        # most recent first, so we get scrape the first item
                        # and let the consumer check the epoch_published. If it
                        # passes, all items in the page will pass as well, even
                        # if their epoch_published is earlier than
                        # epoch_oldest, but that's ok.
                        if not epoch_published:
                            log.info("Scraping and processing first item to get its epoch_published")
                            item = self.scrape(item.native_url)

                            epoch_published = item.bdlitem.epoch_published
                            log.info("Using epoch_published=%s for all items on the scanned page" % epoch_published)

                        else:
                            self.consumer.process(item)

            except ConsumerEpochReachedError:
                log.info("Consumer reached epoch boundary for category %s - Proceed with next category" % category)


    def scrape(self, native_url, scraper_data=None):
        """Parse an announce on Tradera"""

        if not self.get_url(native_url):
            raise CannotGetUrlError("Failed to fetch url %s" % native_url)

        log.debug("Scraping html: %s" % self.html[0:100])

        main = self.get_soup().find(class_='view-item')
        assert main, "Failed to find view-item in %s" % native_url

        # Title and picture
        tag = main.find('div', class_='image-gallery-item')
        assert tag, "Failed to find item image in %s" % native_url
        native_picture_url = tag.img['src']
        title = tag.img['alt']
        assert native_picture_url.startswith('//')

        # Description
        tag = main.find(class_='view-item-description').find(class_='content-text')
        assert tag, "Failed to find description in %s" % native_url
        description = self.html_to_text(str(tag))

        # Epoch of publication?
        tag = main.find(class_='view-item-footer-information-details-published')
        assert tag, "Failed to publication date in footer in %s" % native_url
        s = self.html_to_text(tag.text)
        s = s.split(':', 1)[1].strip()
        date = parser.parse(s + ' CET')
        epoch_published = to_epoch(date)

        # Find price
        def string_to_price(s):
            assert 'kr' in s
            return self.find_number(s)

        price = None
        price_is_fixed = False
        tag = main.find(class_='view-item-fixed-price')
        if tag:
            price = string_to_price(tag.text)
            price_is_fixed = True
        else:
            tag = main.find(class_='view-item-bidding-details')
            tag = tag.find(class_='multi-currency-display--bidding-details')
            price = tag['data-amount-in-sek']
            price = string_to_price(price)

        # Find object id
        tag = main.find(class_='view-item-footer-information-details-itemid')
        assert tag, "Failed to item_id footer in %s" % native_url
        native_doc_id = self.find_number(str(tag))

        # Seller is a shop?
        native_seller_is_shop = False
        tag = main.find(class_='view-item-details-list-seller-icon')
        if tag and 'Butik' in str(tag):
            native_seller_is_shop = True

        # Seller name
        tag = main.find(class_='view-item-details-list-seller-name')
        assert tag, "Failed to find seller name class in %s" % native_url
        tag = tag.span
        native_seller_name = tag.text
        assert native_seller_name, "Failed to find seller name in %s" % native_url

        item = ApiPool.scraper.model.ScrapedObject(
            is_complete=True,
            native_url=native_url,
            bdlitem=ApiPool.scraper.model.BDLItem(
                title=title,
                price=price,
                price_is_fixed=price_is_fixed,
                currency='SEK',
                is_sold=False,
                native_picture_url='https:' + native_picture_url,
                description=description,
                epoch_published=epoch_published,
                native_doc_id=native_doc_id,
                native_seller_is_shop=native_seller_is_shop,
                native_seller_name=native_seller_name,
            )
        )

        log.debug("Scraped Tradera announce: %s" % json.dumps(ApiPool.scraper.model_to_json(item), indent=4))

        return self.consumer.process(item)

    #
    # Internal methods
    #


    def yield_listing_page_items(self):
        """Return all items found in this page. Not that these items are
        incomplete: they lack a description"""

        cards = self.get_soup().find_all(class_='item-card-body')
        log.info("Found %s item cards" % len(cards))

        for a in cards:
            try:
                item = self.card_to_listing_item(a)
            except SkipThisItem:
                log.info("Skipping this card")
                continue
            except ParserError as e:
                report_error(
                    title="TRADERA PARSER ERROR",
                    caught="Error: %s\nDocument:\n%s" % (str(e), a),
                )
                continue

            yield item


    def card_to_listing_item(self, card):

        log.debug("Parsing item-card [%s]" % str(card))

        tag = card.find(class_='item-card-figure')
        native_url = tag.a['href']
        assert native_url
        native_url = BASE_URL + '/' + native_url.lstrip('/')
        if not tag.img:
            native_picture_url = None
            # raise SkipThisItem("Card has no picture")
        else:
            native_picture_url = tag.img['src']
            assert native_picture_url.startswith('//')
            native_picture_url = 'https:' + native_picture_url,

        tag = card.find(class_='item-card-details-price-before-discount')
        price = tag.text
        assert price

        tag = card.find(class_='item-card-details-header')
        title = tag['title']

        # Let's prepare an ItemForSale representing this object
        item = ApiPool.scraper.model.ScrapedObject(
            is_complete=False,
            native_url=native_url,
            bdlitem=ApiPool.scraper.model.BDLItem(
                is_sold=False,
                title=title,
                price=price,
                currency='SEK',
                native_picture_url=native_picture_url,
            )
        )

        log.debug("Generated tradera listing item: %s" % json.dumps(ApiPool.scraper.model_to_json(item), indent=4))

        return item


    def gen_first_page_url(self, category, query=None):
        assert category

        params = {
            'sortBy': 'AddedOn',
        }

        if query:
            params['q'] = query

        return BASE_URL + '/%s?%s' % (category, urlencode(params))


    def get_next_page_url(self):
        """Find the url of the next page and return it, or None if no more pages"""

        # Next page urls look like:
        # <li class="search-pagination-next"><a data-page-index="2" href="/search?categoryId=20&amp;q=stol&amp;paging=MjpBdWN0aW9ufDM5fDc2OlNob3BJdGVtfDl8NDk.&amp;spage=2" rel="next" data-nav>Nästa &raquo;</a></li>
        #
        # And it's missing when the last page is reached

        elems = self.get_soup().find_all('a', class_='page-link', attrs={'rel': 'next'})

        if len(elems) == 0:
            log.info("This is the last page!")
            return None
        elif len(elems) != 1:
            raise ParserError("Did not find the expected previous/next links [%s]" % str(elems))

        href = elems[0].get('href')
        log.info("Found next page! at %s" % href)

        return BASE_URL + href
