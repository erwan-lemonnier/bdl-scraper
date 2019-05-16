import os
import logging
from flask import Flask
from pymacaron import API, letsgo
from scraper.formats import get_custom_formats
from scraper.exceptions import error_reporter

log = logging.getLogger(__name__)

app = Flask(__name__)

def start(port=None, debug=None):

    here = os.path.dirname(os.path.realpath(__file__))
    path_apis = os.path.join(here, "apis")

    api = API(
        app,
        port=port,
        debug=debug,
        formats=get_custom_formats(),
        error_reporter=error_reporter,
    )
    api.load_apis(path_apis)
    api.publish_apis(path='docs')
    api.start(serve=['bdl'])


letsgo(__name__, callback=start)
