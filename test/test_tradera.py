import os
import logging
from pymacaron_core.swagger.apipool import ApiPool
from unittest import TestCase
from bs4 import BeautifulSoup
from scraper.formats import get_custom_formats
from scraper.sources.tradera import TraderaScraper
from scraper.consumer import ItemConsumer
from scraper.exceptions import ConsumerLimitReachedError


log = logging.getLogger(__name__)


class Tests(TestCase):

    def setUp(self):
        ApiPool.add(
            'scraper',
            yaml_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'apis', 'scraper.yaml'),
            formats=get_custom_formats(),
        )
        self.maxDiff = None


    def test_init(self):
        TraderaScraper(source='tradera', consumer=ItemConsumer('tradera'))


    def test_scan_10_items(self):
        # Fetch the last 10 tradera announces and queue them up
        consumer = ItemConsumer('tradera', limit_count=10)
        c = TraderaScraper(
            source='tradera',
            consumer=consumer,
        )

        try:
            c.scan()
        except ConsumerLimitReachedError:
            pass
        else:
            assert 0, "Should have caught a ConsumerLimitReachedError error"

        self.assertEqual(consumer.count_items, 10)


    def assertScrape(self, url, data):
        data['native_url'] = url
        c = TraderaScraper(source='tradera', consumer=ItemConsumer('tradera'))
        item = c.scrape(url)
        j = ApiPool.scraper.model_to_json(item)
        self.assertEqual(j, data)


    def test_scrape__item_cards(self):
        tests = [
            # card / object expected
            [
                # This one has a price with 'kr'
                '<div class="item-card-body item-card-body-newtoday" data-discount-rate="0" data-item-card-body="" data-item-category-id="2305" data-price-before-discount="150" data-search-id="3a1745c7-db40-4e37-b5e7-7a0ad9a97e81"><section class="giftwrap giftwrap-free-shipping hidden" data-item-ribbon="" data-item-ribbon-free-shipping=""><div class="giftwrap-ribbon"><div class="giftwrap-text">Fri frakt!</div></div></section><section class="giftwrap giftwrap-on-display hidden" data-item-ribbon="" data-item-ribbon-on-display=""><div class="giftwrap-ribbon"><div class="giftwrap-text">Utvald!</div></div></section><div class="item-card-image"><figure class="item-card-figure"><a data-item-image-link="" data-nav="" href="/item/2305/351972834/lars-lerin-affisch" id="item_img_351972834"><img alt="Lars Lerin affisch" src="//img.tradera.net/medium/946/310361946_5c073647-1a6e-4374-bb69-e8bcc55b41b5.jpg"/></a></figure></div><div class="item-card-details"><p class="item-card-flash">Ny idag</p><div class="item-card-details-data"><div class="item-card-details-main"><span class="item-card-details-discount-rate">-<span data-item-card-discount-rate="">0</span>%</span><h3 class="item-card-details-header" title="Lars Lerin affisch"><a data-item-link="" data-nav="" href="/item/2305/351972834/lars-lerin-affisch" id="item_351972834">Lars Lerin affisch</a></h3><span class="item-card-details-seller">Anetteeng<span class="item-card-details-seller-divider">|</span>Betyg:         <span class="dsr-good">5</span></span><span class="item-card-details-time-left" data-item-card-details-time-left=""><span>5 jun <span class="timeleft"> 12:20</span></span></span></div><ol class="item-card-numbers"><li class="item-card-details-price-info"><span class="item-card-details-price"><span class="item-card-details-price-before-discount" data-item-card-details-price-before-discount="">150 kr</span><span class="item-card-details-price-amount" data-item-card-details-discount-price="" data-item-card-details-price="">150 kr</span><span class="item-card-details-bids" data-item-card-details-bids="">0 bud</span><div class="multi-currency-display multi-currency-display--item-card multi-currency-active" data-amount-in-sek="150 kr" data-multi-currency-display=""><div class="notranslate">≈ $15.56</div></div></span></li><li class="item-card-details-shipping"><span>+95 kr frakt</span></li></ol></div></div><div class="item-card-icons"><div class="item-card-icon-action wish-list-item"><button class="favorite-action wish-list-selector-add" data-add-to-wish-list=""><span class="font-icon"></span>Spara i minneslistan</button><button class="favorite-action wish-list-selector-remove" data-remove-from-wish-list=""><span class="font-icon"></span>Sparad i minneslistan</button></div></div></div>',
                {
                    "bdlitem": {
                        "has_ended": False,
                        "currency": "SEK",
                        "native_picture_url": "https://img.tradera.net/medium/946/310361946_5c073647-1a6e-4374-bb69-e8bcc55b41b5.jpg",
                        "price": 150,
                        "country": "SE",
                        "language": 'sv',
                        "title": "Lars Lerin affisch"
                    },
                    "native_url": "https://www.tradera.com/item/2305/351972834/lars-lerin-affisch",
                    "is_complete": False,
                }
            ],
            [
                # That one has a price without kr
                '<div class="item-card-body item-card-body-newtoday"><section class="giftwrap giftwrap-free-shipping hidden"><div class="giftwrap-ribbon"><div class="giftwrap-text">Fri frakt!</div></div></section><section class="giftwrap giftwrap-on-display hidden"><div class="giftwrap-ribbon"><div class="giftwrap-text">Utvald!</div></div></section><div class="item-card-image"><figure class="item-card-figure"><a href="/item/341167/351974593/2st-servettringar-royal-albert-"><img alt="2ST SERVETTRINGAR ROYAL ALBERT " data-item-card-image="true" src="//img.tradera.net/medium/557/310363557_2bc1e343-fce8-4297-805b-aca2229fbdb8.jpg"/></a></figure></div><div class="item-card-details"><p class="item-card-flash">Ny idag</p><div class="item-card-details-data"><div class="item-card-details-main"><span class="item-card-details-discount-rate">-<span data-item-card-discount-rate="true">0</span>%</span><div class="item-card-details-header" title="2ST SERVETTRINGAR ROYAL ALBERT "><a href="/item/341167/351974593/2st-servettringar-royal-albert-" id="item_351974593">2ST SERVETTRINGAR ROYAL ALBERT </a></div><span class="item-card-details-seller">antik92<span class="mx-2">|</span><span>Betyg: 4.9</span></span><span class="item-card-details-time-left" data-item-card-details-time-left="true"><span class="">2 jun <span class="timeleft"> 12:44</span></span></span></div><ol class="item-card-numbers"><li class="item-card-details-price-info"><span class="item-card-details-price"><span class="item-card-details-price-amount">55 kr</span><span class="item-card-details-price-before-discount">55</span><span class="item-card-details-bids">0 bud</span></span></li><li class="item-card-details-shipping"><span>+59 kr frakt</span></li></ol></div></div><div class="item-card-icons d-flex align-items-center"><div class="item-card-icon-action wish-list-item wishlist-selector"><button class="favorite-action wish-list-selector-add rounded"><span class="font-icon pr-2"></span>Spara i minneslistan</button></div><div class="d-none d-lg-flex quick-view-icon bg-primary rounded justify-content-center align-items-center"><svg class="icon icon-lg icon-white" height="34" viewbox="0 0 34 34" width="34" xmlns="http://www.w3.org/2000/svg"><path d="M31.88 16.65a.56.56 0 0 1 0 .7l-.76 1.04c-.33.44-1.01 1.21-2.05 2.32a26.79 26.79 0 0 1-3.2 2.94c-1.1.84-2.47 1.61-4.08 2.3A12.1 12.1 0 0 1 17 27c-1.57 0-3.16-.33-4.75-.99A16.55 16.55 0 0 1 8.1 23.6a38.88 38.88 0 0 1-3.15-2.85 19.29 19.29 0 0 1-2.1-2.43l-.73-.97a.56.56 0 0 1 0-.7l.76-1.04c.33-.44 1.01-1.21 2.05-2.32a26.79 26.79 0 0 1 3.2-2.94c1.1-.84 2.46-1.61 4.08-2.3A12.1 12.1 0 0 1 17 7c1.57 0 3.16.33 4.75.99 1.6.66 2.97 1.46 4.13 2.4a40.17 40.17 0 0 1 3.12 2.8 19.9 19.9 0 0 1 2.08 2.35l.73 1 .07.11zM17 22.63a5.4 5.4 0 0 0 3.97-1.65A5.42 5.42 0 0 0 22.62 17c0-1.55-.55-2.88-1.65-3.98A5.4 5.4 0 0 0 17 11.38a5.4 5.4 0 0 0-3.97 1.64A5.42 5.42 0 0 0 11.38 17c0 1.57.54 2.9 1.63 4A5.42 5.42 0 0 0 17 22.61z"></path></svg></div></div></div>',
                {
                    "native_url": "https://www.tradera.com/item/341167/351974593/2st-servettringar-royal-albert-",
                    "bdlitem": {
                        "country": "SE",
                        "language": 'sv',
                        "price": 55,
                        "currency": "SEK",
                        "title": "2ST SERVETTRINGAR ROYAL ALBERT ",
                        "native_picture_url": "https://img.tradera.net/medium/557/310363557_2bc1e343-fce8-4297-805b-aca2229fbdb8.jpg",
                        "has_ended": False
                    },
                    "is_complete": False
                },
            ]

        ]

        for card, want in tests:
            card = BeautifulSoup(card, 'lxml')
            c = TraderaScraper(source='tradera', consumer=ItemConsumer('tradera'))
            i = c.card_to_listing_item(card)
            j = ApiPool.scraper.model_to_json(i)
            self.assertEqual(j, want)
