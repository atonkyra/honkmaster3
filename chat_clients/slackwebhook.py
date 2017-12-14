import logging
import requests
import time
import json


class SlackWebHook(object):
    def __init__(self, config):
        self._config = config
        self._logger = logging.getLogger('slackwebhook')

    def broadcast_message(self, message):
        for hooktarget in self._config['webhook']:
            if '#' not in hooktarget:
                self._logger.error('invalid hook target: %s', hooktarget)
                return
            url, channel = hooktarget.split('#', 1)
            channel = '#%s' % channel
            msg = message
            if 'prefix' in self._config:
                msg = '%s %s' % (self._config['prefix'][-1], message)
            slack_data = {
                'channel': channel,
                'username': self._config['username'][-1],
                'text': msg
            }
            response = requests.post(
                url, data=json.dumps(slack_data),
                headers={'Content-Type': 'application/json'}
            )
            if response.status_code != 200:
                logger.error('slack returned HTTP %s: %s', response.status_code, response.text)

    def register_message_handler(self, message_handler):
        # no-op, we don't eat slack messages
        pass

    def run(self):
        while True:
            time.sleep(1)

__chat_client_class__ = SlackWebHook
