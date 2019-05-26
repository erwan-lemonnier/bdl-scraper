import logging
import requests
import json
import pprint
import socket
from pymacaron.utils import to_epoch, timenow
from pymacaron.config import get_config


log = logging.getLogger(__name__)


HOSTNAME = socket.gethostname()


def slack_info(source, message, channel=None):
    if not channel:
        channel = get_config().slack_channel
    do_slack(
        "%s %s|%s: %s" % (
            str(timenow())[11:19],
            source.upper(),
            HOSTNAME,
            message,
        ),
        channel=channel,
        as_user='SCRAPER',
        emoji=':robot_face:',
        is_real=True,
    )


def do_slack(message, channel=None, as_user='bazardelux.com', emoji=':heart:', is_real=False):
    assert channel

    r = requests.post(
        get_config().slack_url,
        json={
            "channel": "#%s" % channel,
            "username": as_user,
            "text": message,
            "icon_emoji": emoji,
        }
    )

    log.info("Sent message to slack and got: %s" % r.text)

    if r.status_code != requests.codes.ok:
        log.warn("Failed to slack #%s that: (%s) because: %s" % (channel, message, r.text))


def slack_error(title, body):
    assert title
    assert body

    def pp(d):
        return pprint.pformat(d, indent=0).lstrip('{').rstrip('}')

    data = json.loads(body)

    fatal = data['is_fatal_error']
    color = '#F9B01D'
    emoji = ':frowning:'
    if fatal:
        color = '#F9431D'
        emoji = ':skull_and_crossbones:'

    trace = '\n'.join(data.get('trace', ''))
    user_data = pp(data.get('user', ''))
    url = data.get('endpoint', {}).get('url', '')
    response = pp(data.get('response', {}))
    endpoint = pp(data.get('endpoint', {}))

    for k in ('trace', 'user', 'response', 'endpoint', 'error_id', 'is_fatal_error', 'call_id'):
        if k in data:
            del data[k]

    more = pp(data)

    log.info("Will send: [%s]" % endpoint)

    if 'NON-FATAL' in title:
        channel = "#%s" % get_config().slack_warnings_channel
    else:
        channel = "#%s" % get_config().slack_errors_channel

    log.info("Slacking error to channel %s" % channel)

    r = requests.post(
        get_config().slack_url,
        json={
            "channel": channel,
            "username": get_config().live_host,
            "icon_emoji": emoji,
            "attachments": [
                {
                    "fallback": title,
                    "color": color,
                    "pretext": title,
                    "author_name": url,
                    "title": 'Trace',
                    "title_link": "",
                    "text": trace,
                    "fields": [
                        {
                            "title": "Response",
                            "value": response,
                            "short": True,
                        },
                        {
                            "title": "User",
                            "value": user_data,
                            "short": True,
                        },
                        {
                            "title": "Endpoint",
                            "value": endpoint,
                            "short": False,
                        },
                        {
                            "title": "More",
                            "value": more,
                            "short": False,
                        },
                    ],
                    "footer": "Error Report",
                    "ts": to_epoch(timenow()),
                }
            ]
        }
    )

    log.info("Sent message to slack and got: %s" % r.text)

    if r.status_code != requests.codes.ok:
        log.warn("Failed to slack #%s that: (%s) because: %s" % (channel, title, r.text))
