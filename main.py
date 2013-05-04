import datetime, json, re

from google.appengine.api import xmpp
from google.appengine.ext.webapp import xmpp_handlers, template

import webapp2

from webapp2_extras import jinja2

from pibot.rpcclient import RPCClient
from pibot.tpbclient import TPBClient

from pibot.config import AUTHORIZED_USERS

from pibot.futurama_quotes import get_random_quote

RPC_CLIENT = RPCClient()
TPB_CLIENT = TPBClient()

CONVERSATIONS = {}

def bare_jid(sender):
    return sender.split('/')[0]


class XmppHandler(xmpp_handlers.CommandHandler):
    def __init__(self, *args, **kwargs):
        super(XmppHandler, self).__init__(*args, **kwargs)
        self.conversations = CONVERSATIONS

    """Handler class for all XMPP activity."""
    def message_received(self, message):
        sender = bare_jid(message.sender)
        if sender in AUTHORIZED_USERS:
            xmpp_handlers.CommandHandler.message_received(self, message)
        else:
            message.reply(get_random_quote())

    def unhandled_command(self, message=None):
        """Shows help text for commands which have no handler.

        Args:
            message: xmpp.Message: The message that was sent by the user.
        """
        message.reply("Hi I'm Transmibot !")

    def help_command(self, message=None):
        message.reply(template.render('templates/help.html', {}))

    def addtorrent_command(self, message=None):
        if message.arg:
            url = message.arg
            res = RPC_CLIENT.request("torrent-add", {'filename' : url})
            message.reply(json.dumps(res))
        else:
            message.reply("Please provide a URL. What do I look like ? A guy who's not lazy ?")

    def dl_command(self, message=None):
        sender = bare_jid(message.sender)
        if sender in self.conversations:
            index = int(message.arg) - 1
            if index < len(self.conversations[sender]):
                torrent = self.conversations[sender][index]
                res = RPC_CLIENT.request("torrent-add", {'filename' : torrent["magnet"]})
                if res["result"] == "success":
                    message.reply("Added " + torrent["name"])
                else:
                    message.reply("Could not add " + torrent["name"] + ". Result : " + res["result"])
                del self.conversations[sender]
            else:
                message.reply("Index ("+index+") out of bounds") 
        else:
            message.reply("Use search before using the dl command")

    def search_command(self, message=None):
        if message.arg:
            keywords = message.arg
            torrents = TPB_CLIENT.request(keywords)
            if len(torrents) > 0:
                sender = bare_jid(message.sender)
                self.conversations[sender] = torrents
                message.reply(template.render('templates/tpb_list.html', {'tpb_items' : torrents}))
            else:
                message.reply("No torrent found ...")
        else:
            message.reply("I searched the void, nothin' ... Try with keywords maybe ?")

    def best_command(self, message=None):
        if message.arg:
            torrents = TPB_CLIENT.request(message.arg)
            if len(torrents) > 0:
                torrent = torrents[0]
                res = RPC_CLIENT.request("torrent-add", {'filename' : torrent["magnet"]})
                if res["result"] == "success":
                    message.reply("Added " + torrent["name"])
                else:
                    message.reply("Could not add " + torrent["name"] + ". Result : " + res["result"])
            else:
                message.reply("No torrent found ...")
        else:
            message.reply("I searched the void, nothin' ... Try with keywords maybe ?")

    def stop_command(self, message=None):
        # should allow to set a filter, and stop only active torrents that match said filter
        '''Stop all torrents
        '''
        res = RPC_CLIENT.request("torrent-stop", {})
        if res["result"] == "success":
            message.reply("Stopped all torrents still active.")
        else:
            message.reply("Something went horribly wrong. Result : " + res["result"])


    def start_command(self, message=None):
        # idem here : filter
        '''Start unfinished torrents
        '''
        res = RPC_CLIENT.request("torrent-get", {'fields' : ['id', 'percentDone', 'status']})
        torrents = res["arguments"]["torrents"]
        ids = []
        for torrent in torrents:
            if torrent["percentDone"] < 1 and torrent["status"] == 0:
                ids.append(torrent["id"])
        if len(ids) > 0:
            res = RPC_CLIENT.request("torrent-start", {'ids' : ids})
            if res["result"] == "success":
                message.reply("Started all the unfinished torrents ("+str(len(ids))+").")
            else:
                message.reply("Something went horribly wrong. Result : " + res["result"])
        else:
            message.reply("All the torrents are already completed. You don't expect me to seed I hope ?")

    def status_command(self, message=None):
        res = RPC_CLIENT.request("torrent-get", {'fields' : ['name', 'isFinished', 'percentDone', 'status']})
        torrents = res["arguments"]["torrents"]
        if len(torrents) > 0:
            for torrent in torrents:
                torrent["percentDone"] = 100 * torrent["percentDone"]
                torrent["isActive"] = not torrent["isFinished"] and torrent["status"] != 0
                torrent["isNotCompleted"] = torrent["percentDone"] < 100
            all = False
            if message.arg == "all":
                all = True
            message.reply(template.render('templates/status.html', {'torrents' : torrents, 'all' : all}))
        else:
            message.reply("No torrent in the queue")

    def text_message(self, message=""):
        """Called when a message not prefixed by a /cmd is sent to the XMPP bot.

        Args:
            message: xmpp.Message: The message that was sent by the user.
        """

        verb = message.arg.split(" ")[0].lower()
        if verb + "_command" in dir(self):
            post = self.request.POST
            post["body"] = "/" + post["body"]
            getattr(self, verb + "_command")(xmpp.Message(post))
        else:
            self.unhandled_command(message)

    def quote_command(self, message=None):
        """Called on /quote , will return a random futurama quote.

        Args:
            message: xmpp.Message: The message that was sent by the user.
        """
        message.reply(get_random_quote())

APPLICATION = webapp2.WSGIApplication([
        ('/_ah/xmpp/message/chat/', XmppHandler),
        ], debug=True)

