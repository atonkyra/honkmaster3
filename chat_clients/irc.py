import logging
from lib.ircclient import IRCClient
from lib.util import establish_connection
import asyncore


class IRC(object):
    def __init__(self, config):
        self._config = config
        self._build_irc_settings()
        self._logger = logging.getLogger('irc-chat-client')
        ssl = False
        if 'ssl' in config:
            ssl_value = config['ssl'][-1].lower()
            if ssl_value in ['true','1','yes']:
                ssl = True
        self._irc_client = IRCClient(
            self._logger,
            establish_connection(config['server'][-1], config['port'][-1], self._logger, ssl),
            **self._irc_settings
        )

    def _build_irc_settings(self):
        irc_settings = {}
        if 'sever_password' in self._config and self._config['server_password'] is not None:
            irc_settings['server_password'] = self._config['server_password'][-1]
        irc_settings['channels'] = self._config['channel']
        if self._config['nick'] is not None:
            irc_settings['nick'] = self._config['nick'][-1]
        if self._config['realname'] is not None:
            irc_settings['realname'] = self._config['realname'][-1]
        self._irc_settings = irc_settings

    def broadcast_message(self, message):
        self._irc_client.broadcast_message(message)

    def register_message_handler(self, message_handler):
        self._irc_client.register_message_handler(message_handler)

    def run(self):
        asyncore.loop(timeout=0.1)

__chat_client_class__ = IRC
