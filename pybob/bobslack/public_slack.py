#!/usr/bin/env python
"""This uses the App API for slack to post to slack channels.

As of this writing, we use it for the ucsdcse slack, but not for chezbob slack.

"""

import argparse
import sys
import time

from slackclient import SlackClient


from secrets import get_secret


CHANNEL_IDS = {
    "slackbot": "D0DCD2PJ5",
}

SLACK_API_URL = "https://slack.com/api/"

DEFAULT_CHANNEL = "#chezbob"

sc = SlackClient(get_secret("slack.ucsdcse_token"))


def populate_channel_mapping():
    result = sc.api_call("channels.list")
    if not result['ok']:
        return

    for channel in result['channels']:
        CHANNEL_IDS['#' + channel['name']] = channel['id']


def get_channel_id(channel):
    channel_id = CHANNEL_IDS.get(channel, None)
    if not channel_id:
        populate_channel_mapping()
        channel_id = CHANNEL_IDS.get(channel, None)
    return channel_id


def send_msg(message, channel=DEFAULT_CHANNEL, as_user=False):
    channel_id = get_channel_id(channel)

    return sc.api_call(
        "chat.postMessage",
        text=message,
        channel=channel_id,
        as_user=as_user,
    )


def delete_msg(message):
    return sc.api_call(
        "chat.delete",
        channel=message["channel"],
        ts=message["ts"],
    )


def get_slack_id(guesses):
    """Get ID for slack user with any of email prefixes listed in guesses."""

    if not get_slack_id.cached_members:
        response = sc.api_call(
            "users.list",
            presence=False)

        if not response.get("ok", False):
            print("Not OK")
            return None

        get_slack_id.cached_members = response['members']

    for m in get_slack_id.cached_members:
        email = m.get('profile', dict()).get('email', "")
        for guess in guesses:
            if email.startswith(guess + "@"):
                return m['id']
    return None
get_slack_id.cached_members = None


def get_args():

    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--channel', default=DEFAULT_CHANNEL,
                        help="Channel to send to.")
    parser.add_argument('-d', '--delete_after', default=None, type=int,
                        help="Delete after given seconds.")
    parser.add_argument('-u', '--as_user', action='store_true',
                        help="Post as a user. Probably Joe. Don't do that.")
    parser.add_argument('message',
                        help="Message to send")
    return parser.parse_args()


def main():
    args = get_args()

    message = args.message
    if message == "-":
        message = sys.stdin.read()
    result = send_msg(message, channel=args.channel, as_user=args.as_user)

    if args.delete_after:
        time.sleep(args.delete_after)
        delete_msg(result)


if __name__ == "__main__":
    sys.exit(main())


