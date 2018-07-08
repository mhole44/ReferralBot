#!/usr/bin/python
from datetime import datetime, timedelta
import os
import praw
from praw.models import Message
from praw.exceptions import APIException, PRAWException, ClientException
import random
import re
import time
import traceback

try:
    reddit = praw.Reddit(client_id=os.environ["CLIENT_ID"],
                         client_secret=os.environ["CLIENT_SECRET"],
                         password=os.environ["REDDIT_PASSWORD"],
                         user_agent='PM Bot',
                         username=os.environ["REDDIT_USERNAME"])
except KeyError:
    reddit = praw.Reddit('bot1')

# Used in response messages
PM_MOBILE_LINK = "https://productioncommunity.publicmobile.ca/t5/Rewards/Refer-a-Friend-Reward/m-p/411#M4"

USER_MESSAGE_LINK = "https://www.reddit.com/message/compose/?to={username}" \
                    "&subject=PM%20Mobile%20Referral&message=" \
                    "Hello%20{username}!%20The%20PM%20Referral%20Bot%20directed%20me%20to%20you.%20Thanks%20" \
                    "for%20the%20referral%20number!"

BOT_MESSAGE_LINK = "https://www.reddit.com/message/compose?to=/u/PMReferralBot&subject=" \
                   "PM%20Referral&message=Referral%20Please"


class Responder(object):
    """
    Class for responding to a Message for PM Referrals.

    Attributes:
        message (praw.models.Message): Object of Message from user
        _user (str): Author of message
        _replyMessage (str): Message body to send back
        _referer (str); Username of person who will refer the user
    """

    def __init__(self, message):
        self._message = message  # Message
        self._user = message.author
        self._replyMessage = "Hello {user}!".format(user=self._user)

    def run(self):
        """Handles the actions for Responder"""
        print("Responding to {}".format(self._user.name))
        if self._verify() and "re:" not in self._message.subject:
            print("User age verified")
            self._get_referral_user()
            self._build_message()
            self._reply()

    def _verify(self) -> bool:
        """
        Verifies the user's account is older than a day. All time objects use UTC.

        Returns:
            bool: True if self._user's account age is older than a day
        """
        current_time = datetime.utcnow()

        user_created = self._user.created_utc

        one_day = timedelta(days=1)

        return current_time - datetime.fromtimestamp(user_created) > one_day

    def _get_referral_user(self) -> None:
        """
        Gets _user as a randomly selected element from a list of user's who opted in to referring other customers.
        User list here: https://reddit.com/r/PublicMobile/wiki/referrals
        Regex expression taken from
            https://stackoverflow.com/questions/2596771/regex-to-split-on-successions-of-newline-characters
            Ex:
                a = "Foo\r\n\r\nDouble Windows\r\rDouble OS X\n\nDouble Unix\r\nWindows\rOS X\nUnix"
                b = re.split(r'[\r\n]+', a)
                ['Foo', 'Double Windows', 'Double OS X', 'Double Unix', 'Windows', 'OS X', 'Unix']
        """
        page = reddit.subreddit("PublicMobile").wiki['referrals']
        users_string = page.mod.wikipage.content_md
        users = re.split(r'[\r\n]+', users_string)

        self._referer = random.sample(users, 1)[0]

    def _build_message(self):
        """Build the response to the user."""

        if self._message.subject in ["PM Referral"]:
            # Give them a referral
            message_referer_link = USER_MESSAGE_LINK.format(username=self._referer)
            self._replyMessage += \
                " Thanks for showing interest in Public Mobile. When signing up," \
                " you can get a referral number from {referer}. Click [here]({message_referer_link}) to " \
                "message {referer}. \n\n Alternatively, click [here]({pm_referrals_link}) to get more information " \
                "on how referrals work.".format(
                    referer=self._referer,
                    message_referer_link=message_referer_link,
                    pm_referrals_link=PM_MOBILE_LINK)
        elif "re:" in self._message.subject:
            # They are responding to our _message. What to do?
            print("User {} replied to our _message. This is the _message: \n"
                  "Subject: {} \n Message Body: {}".format(self._user, self._message.subject, self._message.body))
        else:
            # Tell them more about PM Mobile
            self._replyMessage += \
                " I am a bot that can help you get a referral number for Public Mobile." \
                " We have a list of Public Mobile users who are happy to have their number used" \
                " for referrals. If you want to get a referral number, send me a message with \"PM Referral\"" \
                " as the subject or alternatively click [here]({bot_link}).".format(bot_link=BOT_MESSAGE_LINK)

    def _reply(self):
        """Send a reply to the user"""

        def send_message():
            self._message.reply(self._replyMessage)

        try:
            send_message()
            print("Message send successful to {}".format(self._user))
        except (APIException, PRAWException, ClientException) as e:
            print(e)

            # In case of RateLimitExceeded
            time.sleep(10)
            send_message()
            print("Message send successful")
        except Exception as e:
            print("Didn't send message. This is why: \n {}".format(e))


def handle():
    print("Starting...")
    while True:
        print("Checking inbox...")
        try:
            for item in reddit.inbox.unread(limit=100):
                if isinstance(item, Message):
                    pm = Responder(item)
                    pm.run()
                    item.mark_read()
            time.sleep(30)
            print("Sleeping...")
        except Exception:
            print("Error occurred. Here's the traceback: \n {} \n\n Sleeping for 30 seconds then "
                  "continuing on...".format(traceback.format_exc()))
            time.sleep(30)


if __name__ == "__main__":
    handle()
