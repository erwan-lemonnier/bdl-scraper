import os
import logging
from pymacaron_core.swagger.apipool import ApiPool
from scraper.formats import get_custom_formats
from unittest import TestCase
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
                }
            }
        )
