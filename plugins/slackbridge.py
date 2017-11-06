import re
import logging
import json
import time
from slackclient import SlackClient

logger = logging.getLogger('slackbridge')

class SlackBridge(object):
    __name__ = "SlackBridge"

    def __init__(self, arg):
        token, channel = arg.split(';')
        self._channel = channel
        self._sc = SlackClient(token)
        self._sc.rtm_connect(with_team_state=False)
        self._user_cache = {}

    def handle_message(self, msg):
        if msg['action'] == 'PRIVMSG':
            nick = msg['source'].split('!', 1)[0]
            message = msg['data']
            self._sc.api_call(
                'chat.postMessage',
                channel=self._channel,
                text='%s' % (message),
                username=nick
            )

    def update_user_cache(self):
        res = self._sc.api_call('users.list')
        if 'members' in res:
            for member_info in res['members']:
                try:
                    self._user_cache[member_info['id']] = member_info['profile']['display_name_normalized']
                except:
                    self._user_cache[member_info['id']] = member_info['id']


    def get_user(self, user_id):
        ret = user_id
        if user_id not in self._user_cache:
            self.update_user_cache()
        if user_id in self._user_cache:
            return self._user_cache[user_id]
        return ret


    def replacer(self, re_line):
        gdict = re_line.groupdict()
        if 'userid' in gdict:
            return self.get_user(gdict['userid'])
        return ''


    def get_messages(self):
        while True:
            events = self._sc.rtm_read()
            for event in events:
                if 'type' in event and event['type'] == 'message' and 'text' in event and 'user' in event:
                    if 'upload' in event and event['upload'] == True and 'file' in event and 'permalink' in event['file']:
                        nick = self.get_user(event['user'])
                        yield '%s uploaded a file: %s' % (nick, event['file']['permalink'])
                    else:
                        if 'subtype' in event:
                            logger.info('unhandled event subtype: %s', event['subtype'])
                            logger.info('%s', json.dumps(event))
                            continue
                        messages = event['text'].split('\n')
                        nick = self.get_user(event['user'])
                        for message in messages:
                            message_formatted = re.sub(r'<@(?P<userid>\w+)>', self.replacer, message)
                            yield '<%s> %s' % (nick, message_formatted)
            if len(events) == 0:
                time.sleep(1)

__plugin_class__ = SlackBridge
