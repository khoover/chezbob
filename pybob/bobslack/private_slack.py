#!/usr/bin/env python
"""This script posts to our private slack.

We use legacy slack webhooks on chezbob slack because it's more flexible.

We've moved to the new app API for the ucsdcse slack. That's probably the right
answer for our private slack too, but for now we have both...
"""

import argparse
import json
import http.client
import sys


from secrets import get_secret


POST_PATH = "/services/T0B8HGL80/B1H1A7RM0/"
USER = "BobBot"
ICON = ":homerpanic:"
DEFAULT_CHANNEL = "#random"

POST_HOST = "hooks.slack.com"


def send_msg(message, channel=DEFAULT_CHANNEL, icon=ICON):
    conn = http.client.HTTPSConnection(POST_HOST)

    body = {
        "text": message,
        "username": USER,
        "icon_emoji": icon,
        "channel": channel,
        "mrkdwn": True,
    }

    post_path = POST_PATH + get_secret("slack.chezbob_token")

    conn.request(
        "POST", post_path, json.dumps(body),
        {"Content-type": "application/json"})

    return conn.getresponse().read()


def get_args():

    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--channel', default=DEFAULT_CHANNEL,
                        help="Channel to send to.")
    parser.add_argument('message',
                        help="Message to send.")
    return parser.parse_args()


def main():
    args = get_args()

    message = args.message
    if message == "-":
        message = sys.stdin.read()
    result = send_msg(message, channel=args.channel)

    print(result)


if __name__ == "__main__":
    sys.exit(main())


