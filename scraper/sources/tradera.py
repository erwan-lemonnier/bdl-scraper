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
from scraper.exceptions import ConsumerLimitReachedError


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

                        # The listing page does not show the publication time of the announce,
                        # but we know that they are listed by most recent first, so we get scrape
                        # the first item and set the publication epoch of all items on that page
                        # to that of the first one.
                        if not epoch_published:
                            i = self.scrape(item.native_url)
                            epoch_published = i.epoch_published

                        item.epoch_published = epoch_published

                        self.consumer.process_and_go_on(item)

            except ConsumerLimitReachedError:
                log.info("Consumer limit reached for category %s - Proceed with next category" % category)


    def scrape(self, native_url):
        """Parse an announce on Tradera"""

        if not self.get_url(native_url):
            raise CannotGetUrlError("Failed to fetch url %s" % native_url)

        main = self.get_soup().find(class_='view-item')
        assert main, "Failed to find view-item-main in %s" % native_url

        tags = main.find_all('img', class_='image-gallery-item__image')
        assert len(tags) > 0, "Failed to find main image in %s" % native_url
        tag = tags[0]
        native_picture_url = tag['src']
        title = tag['alt']

        native_picture_url = native_picture_url
        assert native_picture_url.startswith('//')

        tag = main.find(class_='view-item-description').find(class_='content-text')
        assert tag, "Failed to find description in %s" % native_url
        description = self.html_to_text(str(tag))

        tag = main.find(class_='view-item-footer-information-details-published')
        assert tag, "Failed to publication date in footer in %s" % native_url
        s = self.html_to_text(tag.text)
        s = s.split(':', 1)[1].strip()
        date = parser.parse(s + ' CET')
        epoch_published = to_epoch(date)

        def string_to_price(s):
            assert 'kr' in s
            s = s.replace('kr', '').strip()
            s = self.html_to_text(s)
            s = s.replace(' ', '')
            return int(s)

        # Find price
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

        item = ApiPool.scraper.model.TraderaItem(
            native_url=native_url,
            native_picture_url='https:' + native_picture_url,
            is_sold=None,
            title=title,
            description=description,
            price=price,
            price_is_fixed=price_is_fixed,
            currency='SEK',
            epoch_published=epoch_published,
        )

        log.debug("Scraped Tradera announce: %s" % json.dumps(ApiPool.scraper.model_to_json(item), indent=4))

        return item

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

        log.debug("Parsing [%s]" % str(card))

        tag = card.find(class_='item-card-figure')
        log.info("Found card_figure: %s" % tag)
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
        log.debug("title tag: %s" % tag)
        title = tag['title']

        # Let's prepare an ItemForSale representing this object
        item = ApiPool.scraper.model.TraderaListingItem(
            title=title,
            native_url=native_url,
            native_picture_url=native_picture_url,
            price=price,
            currency='SEK',
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

        log.info("SEARCHING FOR NEXT PAGE")

        # Next page urls look like:
        # <li class="search-pagination-next"><a data-page-index="2" href="/search?categoryId=20&amp;q=stol&amp;paging=MjpBdWN0aW9ufDM5fDc2OlNob3BJdGVtfDl8NDk.&amp;spage=2" rel="next" data-nav>Nästa &raquo;</a></li>
        #
        # And it's missing when the last page is reached

        elems = self.get_soup().find_all('a', class_='page-link', attrs={'rel': 'next'})

        log.debug("Found elems: %s" % elems)

        if len(elems) == 0:
            log.info("This is the last page!")
            return None
        elif len(elems) != 1:
            raise ParserError("Did not find the expected previous/next links [%s]" % str(elems))

        href = elems[0].get('href')
        log.info("Found next page! at %s" % href)

        return BASE_URL + href
