import asynchat
import StringIO
import logging
import random
import time


IRCStatusMap = {
    '001': 'WELCOME',
    '002': 'YOURHOST',
    '003': 'CREATED',
    '004': 'MYINFO',
    '005': 'PROTOCOL',
    '042': 'YOURID',
    '251': 'LUSERCLIENT',
    '252': 'LUSEROP',
    '253': 'LUSERUNKNOWN',
    '254': 'LUSERCHANNELS',
    '255': 'LUSERME',
    '265': 'LOCALUSERS',
    '266': 'GLOBALUSERS',
    '372': 'MOTD',
    '375': 'MOTDSTART',
    '376': 'ENDOFMOTD',
    '433': 'NICKINUSE'
}
logger = logging.getLogger('ircclient')

def user_set_or_default(default_value, key, settings_dict):
    if key in settings_dict:
        return settings_dict[key]
    return default_value


class IRCClient(asynchat.async_chat):
    def __init__(self, skt, **kwargs):
        asynchat.async_chat.__init__(self, sock=skt)
        self.set_terminator(b'\n')
        self._rbuf = StringIO.StringIO()
        self._irc_settings = {}
        self._joined_channels = []
        for k,v in kwargs.iteritems():
            self._irc_settings[k] = v
        self._queue_initial_irc_connection_commands()
        self._ready = False

    def _send_message_to_channel(self, channel, msg):
        self._encsendline('PRIVMSG %s :%s' % (channel, msg))

    def broadcast_message(self, msg):
        if not self._ready:
            logger.debug("defer message until ready: %s", msg)
        while not self._ready:
            time.sleep(1)
        for channel in self._joined_channels:
            self._send_message_to_channel(channel, msg)

    def _queue_initial_irc_connection_commands(self):
        s = self._irc_settings
        if 'server_password' in s:
            self._encsendline('PASS %s' % (s['server_password']))
        nick = user_set_or_default('HonkMaster3', 'nick', s)
        self._encsendline('NICK %s' % (nick))
        realname = user_set_or_default('HonkMaster3', 'realname', s)
        self._encsendline('USER %(nick)s %(nick)s %(nick)s :%(realname)s' % {'nick': nick, 'realname': realname})

    def _queue_channel_joins(self):
        if 'channels' in self._irc_settings:
            if isinstance(self._irc_settings['channels'], list):
                for channel_info in self._irc_settings['channels']:
                    join_settings = {}
                    if isinstance(channel_info, tuple):
                        join_settings['channel'] = channel_info[0]
                        join_settings['password'] = channel_info[1]
                    elif isinstance(channel_info, basestring):
                        join_settings['channel'] = channel_info
                    if 'channel' in join_settings:
                        if 'password' in join_settings:
                            self._encsendline("JOIN %(channel)s %(password)s" % join_settings)
                        else:
                            self._encsendline("JOIN %(channel)s" % join_settings)
            else:
                logger.error("channels argument is not list, skipping channel joins")

    def _encsendline(self, data):
        try:
            linedata = "%s\r\n" % (data)
            self.push(linedata.encode('utf-8'))
            logger.debug("-> %s", linedata.strip())
        except BaseException as be:
            logger.error("error while sending data: %s" % (be))

    def _handle_channel_join(self, msg):
        logger.info("joined %s" % (msg['target']))
        self._joined_channels.append(msg['target'])

    def _handle_server_message(self, msg):
        if msg['action'] == 'NICKINUSE':
            nick = user_set_or_default('HonkMaster3', 'nick', self._irc_settings)
            rand_from_nick = "%s-%s" % (nick, random.randint(0,100))
            altnick = user_set_or_default(rand_from_nick, 'altnick', self._irc_settings)
            self._encsendline("NICK %s" % (altnick))
        if msg['action'] == 'ENDOFMOTD':
            self._queue_channel_joins()
        if msg['action'] == 'JOIN':
            self._handle_channel_join(msg)
            self._ready = True

    def _parse_server_message(self, msg):
        if msg.startswith('PING'):
            challenge = msg.split(':')[1].strip()
            self._encsendline('PONG :%s' % (challenge))
            logger.info("ping %s? pong %s!", challenge, challenge)
            return
        source = None
        action = None
        target = None
        rest = None
        try:
            source, action, target, rest = msg.split(' ', 3)
            source = source.strip()
            action = action.strip()
            target = target.strip()
            rest = rest.strip()
        except:
            source, action, target = msg.split(' ', 3)
            source = source.strip()
            action = action.strip()
            target = target.strip()
        if source.startswith(':'):
            source = source[1:]
        if target.startswith(':'):
            target = target[1:]
        if rest is not None and rest.startswith(':'):
            rest = rest[1:]
        if action.isdigit():
            if action in IRCStatusMap:
                action = IRCStatusMap[action]
            else:
                action = 'UNK%s' % (action)
        self._handle_server_message({'source': source, 'action': action, 'target': target, 'data': rest})

    def collect_incoming_data(self, data):
        self._rbuf.write(data)

    def found_terminator(self):
        msg = self._rbuf.getvalue()
        self._rbuf.truncate(0)
        try:
            msg_decoded = msg.decode('utf-8', errors='ignore')
            logger.debug("<- %s", msg_decoded.strip())
            self._parse_server_message(msg_decoded)
        except BaseException as be:
            logger.exception(be)
            logger.error("failed to parse line from server: %s", msg)
