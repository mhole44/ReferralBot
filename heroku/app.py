#!/usr/bin/python
import os
import pprint

import praw
from praw.models import Comment, Message, Redditor
from praw.exceptions import APIException, PRAWException, ClientException

import items.examples as examples

try:
    reddit = praw.Reddit(client_id=os.environ["CLIENT_ID"],
                         client_secret=os.environ["CLIENT_SECRET"],
                         password=os.environ["REDDIT_PASSWORD"],
                         user_agent='PM Bot',
                         username=os.environ["REDDIT_USERNAME"])
except KeyError:
    reddit = praw.Reddit('bot1')


class Responder(object):
    """
    Attributes:
        message (Message): DM
    """

    def __init__(self, message, is_message=True):
        self.message = message  # Message
        self.is_message = is_message
        self._replyMessage = "Hello {user}!"

    def run(self):
        self.build_message()
        self.reply()

    def build_message(self):
        if self.is_message:
            if self.message.subject in examples.messsages:
                self._replyMessage = examples.messsages[self.message.subject]
            else:
                self._replyMessage = "This is my example message from your PM."
        else:
            self._replyMessage = "This is my response to your comment!"

        self._replyMessage = self._replyMessage.format(
            user=self.message.author)

    def reply(self):
        author = self.message.author

        def send_message():
            if self.is_message:
                self.message.reply(self._replyMessage)
            else:
                author.message("My test subject", examples.messsages["My test subject"])
        try:
            send_message()
            print("Message send successful")
        except (APIException, PRAWException, ClientException) as e:
            print(e)
            pass


def handle():
    for item in reddit.inbox.unread(limit=100):

        if item.author == "mhole45":
            pm = None
            if isinstance(item, Message):
                pm = Responder(item, True)
            elif isinstance(item, Comment):
                pm = Responder(item, False)
            if pm:
                pm.run()
                item.mark_read()

import inspect

if __name__ == "__main__":
    user = reddit.redditor('IEpicDestroyer')
    for i in inspect.getmembers(user):
        print(i)
    print(dir(Redditor))
    print(user.link_karma)
    #pprint.pprint(vars(user))
    while True:
        handle()
