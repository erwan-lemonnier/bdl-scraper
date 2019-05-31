import os
import imp
import logging


common = imp.load_source('common', os.path.join(os.path.dirname(__file__), 'common.py'))


log = logging.getLogger(__name__)


class Tests(common.ScraperTests):

    def test_v1_scraper_scan__tradera__auth_required(self):
        self.assertPostReturnError(
            'v1/scraper/scan',
            {'source': 'TEST'},
            401,
            'AUTHORIZATION_HEADER_MISSING',
        )

    def test_v1_scraper_scan__tradera__live__10_items(self):
        j = self.assertPostReturnJson(
            'v1/scraper/scan',
            {
                'source': 'TRADERA',
                'limit_count': 10,
                'synchronous': True,
            },
            auth='Bearer %s' % self.token,
        )

        objects = j['objects']
        self.assertEqual(len(objects), 10)

        j['objects'] = []
        self.assertEqual(
            j,
            {
                'source': 'TRADERA',
                'real': True,
                'index': 'BDL',
                'objects': [],
            }
        )

        j = objects.pop(0)
        self.assertIsCompleteTraderaItem(j)

        for j in objects:
            self.assertIsIncompleteTraderaItem(j)


    def test_v1_scraper_scrape__tradera__html__no_bid__shop(self):
        j = self.assertPostReturnJson(
            'v1/scraper/scrape',
            {
                'source': 'TRADERA',
                'native_url': 'doesnotmatter',
                'html': self.load_html('tradera__no_bid__shop.html'),
                'synchronous': True,
            },
            auth='Bearer %s' % self.token,
        )

        self.assertEqual(
            j,
            {
                'source': 'TRADERA',
                'real': True,
                'index': 'BDL',
                'objects': [
                    {
                        "bdlitem": {
                            "currency": "SEK",
                            "description": "M\u00e4rke: Royal Caribbean International\nTyp: Termosmugg\nF\u00e4rg: Flerf\u00e4rgad\n\u00d6vrigt: L\u00e4ngd i cm: 20\nVaran \u00e4r ny i originalf\u00f6rpackning / med lapp kvar.\n**Skick:**\nVaran s\u00e4ljs i befintligt skick och endast det som syns p\u00e5 bilderna ing\u00e5r om ej\nannat anges. Vi v\u00e4rderar samtliga varor och ger dom en beskrivning av skicket.\n**Defekter:**\nSkulle en vara s\u00e4ljs med en defekt som g\u00f6r att n\u00e5gon detalj avviker fr\u00e5n det\nf\u00f6rv\u00e4ntade skicket t.ex. fl\u00e4ckar eller h\u00e5l, beskrivs denna tydligt i annonsen\ntillsammans med skickbeskrivningen och \u00e4r inte giltig anledning till en\nreklamation.\n**Betalning:**\nBetalning sker med kort eller bankgiro p\u00e5 v\u00e5r hemsida. Instruktioner skickas\np\u00e5 mail. Efter avslutad auktion ska varan betalas omg\u00e5ende, dock senast inom 3\ndagar.\n**Samfrakt:**\nVi samfraktar g\u00e4rna alla auktioner som g\u00e5r ut senast 2 dagar efter det att du\nvinner den f\u00f6rsta auktionen. Vinner du fler auktioner, v\u00e4nligen inv\u00e4nta\nbetalning innan du f\u00e5r bekr\u00e4ftelsen p\u00e5 mail fr\u00e5n oss.\n**Om Sellpy:**\nDu packar din p\u00e5se med det du vill s\u00e4lja - vi h\u00e4mtar vid d\u00f6rren och sk\u00f6ter\nf\u00f6rs\u00e4ljningen \u00e5t dig. Ge dina saker ett nytt hem!\n**14 dagars \u00e5ngerr\u00e4tt:**\nSom k\u00f6pare har du 14 dagars \u00e5ngerr\u00e4tt enligt lag om distansavtal och avtal\nutanf\u00f6r aff\u00e4rslokaler (SFS 2005:59) n\u00e4r du k\u00f6per fr\u00e5n oss p\u00e5 Sellpy. Vid retur\n\u00e4r det du som k\u00f6pare som st\u00e5r f\u00f6r frakten och vi \u00e5terbetalar pengarna inom 30\ndagar. Detta betyder att du som k\u00f6pare kan k\u00e4nna en trygghet n\u00e4r du k\u00f6per\nvaror fr\u00e5n oss p\u00e5 Sellpy, d\u00e5 du som k\u00f6pare har r\u00e4tten att \u00e5ngra ditt k\u00f6p om\nvaran inte uppfyller de f\u00f6rv\u00e4ntningar du hade p\u00e5 den n\u00e4r du genomf\u00f6rde k\u00f6pet.\n**Leverans:**\nVaran skickas v\u00e4l f\u00f6rpackad och emballerad. Vi erbjuder olika fraktalternativ\noch ordern skickas s\u00e5 snabbt som m\u00f6jligt.\nLycka till!",
                            "epoch_published": 1557995340,
                            "has_ended": False,
                            "native_doc_id": '351064059',
                            "native_picture_url": "https://img.tradera.net/images/405/309549405_518ee380-446e-465f-ab9a-4b29aead7de3.jpg",
                            "native_seller_is_shop": True,
                            "native_seller_name": "Sellpy",
                            "price": 50,
                            "price_is_fixed": True,
                            "title": "Royal Caribbean International, Termosmugg, Flerf\u00e4rgad",
                            "country": "SE",
                            "language": "sv",
                        },
                        "is_complete": True,
                        "native_url": "doesnotmatter"
                    }
                ]
            }
        )


    def test_v1_scraper_scrape__tradera__html__many_bids(self):
        j = self.assertPostReturnJson(
            'v1/scraper/scrape',
            {
                'source': 'TRADERA',
                'native_url': 'doesnotmatter',
                'html': self.load_html('tradera__many_bids.html'),
                'synchronous': True,
            },
            auth='Bearer %s' % self.token,
        )

        self.assertEqual(
            j,
            {
                'source': 'TRADERA',
                'real': True,
                'index': 'BDL',
                'objects': [
                    {
                        "bdlitem": {
                            "currency": "SEK",
                            "description": "Lila mini K\u00e5nken fr\u00e5n Fj\u00e4llr\u00e4ven. V\u00e4l anv\u00e4nd. Se bilderna.\nKommer fr\u00e5n r\u00f6k och djurfritt hem",
                            "epoch_published": 1557079800,
                            "has_ended": False,
                            "native_doc_id": '349772619',
                            "native_picture_url": "https://img.tradera.net/images/631/308398631_3f5f39d6-4ec4-4b25-92d6-250b2b9d2c08.jpg",
                            "native_seller_is_shop": False,
                            "native_seller_name": "Martin Eddy",
                            "price": 280,
                            "price_is_fixed": False,
                            "title": "Mini K\u00e5nken Fj\u00e4llr\u00e4ven, lila",
                            "country": "SE",
                            "language": "sv",
                        },
                        "is_complete": True,
                        "native_url": "doesnotmatter"
                    }
                ],
            }
        )


    def test_v1_scraper_scrape__tradera__ended__no_bid__shop(self):
        j = self.assertPostReturnJson(
            'v1/scraper/scrape',
            {
                'source': 'TRADERA',
                'native_url': 'doesnotmatter',
                'html': self.load_html('tradera__ended__no_bid__shop.html'),
                'synchronous': True,
            },
            auth='Bearer %s' % self.token,
        )

        self.assertEqual(
            j,
            {
                'source': 'TRADERA',
                'real': True,
                'index': 'BDL',
                'objects': [
                    {
                        "bdlitem": {
                            "has_ended": True,
                            "date_ended": "2019-05-30T10:31:00+00:00",
                        },
                        "is_complete": False,
                        "native_url": "doesnotmatter"
                    }
                ]
            }
        )
