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


    def test_scrape__fast_price(self):
        self.assertScrape(
            'https://www.tradera.com/item/340952/351064059/royal-caribbean-international-termosmugg-flerfargad',
            {
                "is_complete": True,
                "bdlitem": {
                    "is_sold": False,
                    "description": "M\u00e4rke: Royal Caribbean International\nTyp: Termosmugg\nF\u00e4rg: Flerf\u00e4rgad\n\u00d6vrigt: L\u00e4ngd i cm: 20\nVaran \u00e4r ny i originalf\u00f6rpackning / med lapp kvar.\n**Skick:**\nVaran s\u00e4ljs i befintligt skick och endast det som syns p\u00e5 bilderna ing\u00e5r om ej\nannat anges. Vi v\u00e4rderar samtliga varor och ger dom en beskrivning av skicket.\n**Defekter:**\nSkulle en vara s\u00e4ljs med en defekt som g\u00f6r att n\u00e5gon detalj avviker fr\u00e5n det\nf\u00f6rv\u00e4ntade skicket t.ex. fl\u00e4ckar eller h\u00e5l, beskrivs denna tydligt i annonsen\ntillsammans med skickbeskrivningen och \u00e4r inte giltig anledning till en\nreklamation.\n**Betalning:**\nBetalning sker med kort eller bankgiro p\u00e5 v\u00e5r hemsida. Instruktioner skickas\np\u00e5 mail. Efter avslutad auktion ska varan betalas omg\u00e5ende, dock senast inom 3\ndagar.\n**Samfrakt:**\nVi samfraktar g\u00e4rna alla auktioner som g\u00e5r ut senast 2 dagar efter det att du\nvinner den f\u00f6rsta auktionen. Vinner du fler auktioner, v\u00e4nligen inv\u00e4nta\nbetalning innan du f\u00e5r bekr\u00e4ftelsen p\u00e5 mail fr\u00e5n oss.\n**Om Sellpy:**\nDu packar din p\u00e5se med det du vill s\u00e4lja - vi h\u00e4mtar vid d\u00f6rren och sk\u00f6ter\nf\u00f6rs\u00e4ljningen \u00e5t dig. Ge dina saker ett nytt hem!\n**14 dagars \u00e5ngerr\u00e4tt:**\nSom k\u00f6pare har du 14 dagars \u00e5ngerr\u00e4tt enligt lag om distansavtal och avtal\nutanf\u00f6r aff\u00e4rslokaler (SFS 2005:59) n\u00e4r du k\u00f6per fr\u00e5n oss p\u00e5 Sellpy. Vid retur\n\u00e4r det du som k\u00f6pare som st\u00e5r f\u00f6r frakten och vi \u00e5terbetalar pengarna inom 30\ndagar. Detta betyder att du som k\u00f6pare kan k\u00e4nna en trygghet n\u00e4r du k\u00f6per\nvaror fr\u00e5n oss p\u00e5 Sellpy, d\u00e5 du som k\u00f6pare har r\u00e4tten att \u00e5ngra ditt k\u00f6p om\nvaran inte uppfyller de f\u00f6rv\u00e4ntningar du hade p\u00e5 den n\u00e4r du genomf\u00f6rde k\u00f6pet.\n**Leverans:**\nVaran skickas v\u00e4l f\u00f6rpackad och emballerad. Vi erbjuder olika fraktalternativ\noch ordern skickas s\u00e5 snabbt som m\u00f6jligt.\nLycka till!",
                    "epoch_published": 1557995340,
                    "title": "Royal Caribbean International, Termosmugg, Flerfärgad",
                    "native_picture_url": "https://img.tradera.net/images/405/309549405_518ee380-446e-465f-ab9a-4b29aead7de3.jpg",
                    "currency": "SEK",
                    "price": 50,
                    "price_is_fixed": True,
                    "native_seller_is_shop": True,
                    "native_seller_name": "Sellpy",
                    "native_doc_id": '351064059',
                    "country": 'SE',
                    "language": 'sv',
                }
            }
        )


    def test_scrape__item_cards(self):
        tests = [
            # card / object expected
            [
                # This one has a price with 'kr'
                '<div class="item-card-body item-card-body-newtoday" data-discount-rate="0" data-item-card-body="" data-item-category-id="2305" data-price-before-discount="150" data-search-id="3a1745c7-db40-4e37-b5e7-7a0ad9a97e81"><section class="giftwrap giftwrap-free-shipping hidden" data-item-ribbon="" data-item-ribbon-free-shipping=""><div class="giftwrap-ribbon"><div class="giftwrap-text">Fri frakt!</div></div></section><section class="giftwrap giftwrap-on-display hidden" data-item-ribbon="" data-item-ribbon-on-display=""><div class="giftwrap-ribbon"><div class="giftwrap-text">Utvald!</div></div></section><div class="item-card-image"><figure class="item-card-figure"><a data-item-image-link="" data-nav="" href="/item/2305/351972834/lars-lerin-affisch" id="item_img_351972834"><img alt="Lars Lerin affisch" src="//img.tradera.net/medium/946/310361946_5c073647-1a6e-4374-bb69-e8bcc55b41b5.jpg"/></a></figure></div><div class="item-card-details"><p class="item-card-flash">Ny idag</p><div class="item-card-details-data"><div class="item-card-details-main"><span class="item-card-details-discount-rate">-<span data-item-card-discount-rate="">0</span>%</span><h3 class="item-card-details-header" title="Lars Lerin affisch"><a data-item-link="" data-nav="" href="/item/2305/351972834/lars-lerin-affisch" id="item_351972834">Lars Lerin affisch</a></h3><span class="item-card-details-seller">Anetteeng<span class="item-card-details-seller-divider">|</span>Betyg:         <span class="dsr-good">5</span></span><span class="item-card-details-time-left" data-item-card-details-time-left=""><span>5 jun <span class="timeleft"> 12:20</span></span></span></div><ol class="item-card-numbers"><li class="item-card-details-price-info"><span class="item-card-details-price"><span class="item-card-details-price-before-discount" data-item-card-details-price-before-discount="">150 kr</span><span class="item-card-details-price-amount" data-item-card-details-discount-price="" data-item-card-details-price="">150 kr</span><span class="item-card-details-bids" data-item-card-details-bids="">0 bud</span><div class="multi-currency-display multi-currency-display--item-card multi-currency-active" data-amount-in-sek="150 kr" data-multi-currency-display=""><div class="notranslate">≈ $15.56</div></div></span></li><li class="item-card-details-shipping"><span>+95 kr frakt</span></li></ol></div></div><div class="item-card-icons"><div class="item-card-icon-action wish-list-item"><button class="favorite-action wish-list-selector-add" data-add-to-wish-list=""><span class="font-icon"></span>Spara i minneslistan</button><button class="favorite-action wish-list-selector-remove" data-remove-from-wish-list=""><span class="font-icon"></span>Sparad i minneslistan</button></div></div></div>',
                {
                    "bdlitem": {
                        "is_sold": False,
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
                        "is_sold": False
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
