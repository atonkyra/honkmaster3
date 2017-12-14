try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO
import asynchat
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


def user_set_or_default(default_value, key, settings_dict):
    if key in settings_dict:
        return settings_dict[key]
    return default_value


def _get_nick_from_source(source):
    return source.split('!')[0]


class IRCClient(asynchat.async_chat):
    def __init__(self, logger, skt, **kwargs):
        self._logger = logger
        asynchat.async_chat.__init__(self, sock=skt)
        self.set_terminator(b'\n')
        self._rbuf = None
        try:
            self._rbuf = StringIO.StringIO()
        except AttributeError:
            self._rbuf = StringIO()
        self._irc_settings = {}
        self._message_handlers = []
        self._joined_channels = []
        self._rate_control_value = 0
        self._rate_control_last_message_at = 0
        self._rate_control_limiting = False
        self._rate_control_discard_count = 0
        self._ready = False
        self._selected_nick = None
        for k in kwargs.keys():
            self._irc_settings[k] = kwargs[k]
        self._queue_initial_irc_connection_commands()

    def _send_message_to_channel(self, channel, msg):
        self._encsendline('PRIVMSG %s :%s' % (channel, msg))

    def _queue_initial_irc_connection_commands(self):
        s = self._irc_settings
        if 'server_password' in s:
            self._encsendline('PASS %s' % (s['server_password']))
        nick = user_set_or_default('HonkMaster3', 'nick', s)
        self._encsendline('NICK %s' % nick)
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
                    elif isinstance(channel_info, str):
                        join_settings['channel'] = channel_info
                    if 'channel' in join_settings:
                        if 'password' in join_settings:
                            self._encsendline("JOIN %(channel)s %(password)s" % join_settings)
                        else:
                            self._encsendline("JOIN %(channel)s" % join_settings)
            else:
                self._logger.error("channels argument is not list, skipping channel joins")

    def _encsendline(self, data, force=False):
        if self._ready:
            cur_time = time.time()
            diff_time = cur_time - self._rate_control_last_message_at
            self._rate_control_last_message_at = cur_time
            self._rate_control_value = max(0.0, self._rate_control_value - diff_time)
            if self._rate_control_limiting and self._rate_control_value == 0.0:
                self._logger.info("cleared rate-limit, %s messages discarded", self._rate_control_discard_count)
                self._rate_control_discard_count = 0
                self._rate_control_limiting = False
            if not self._rate_control_limiting:
                self._rate_control_value += 3
                if self._rate_control_value > 40.0 and not self._rate_control_limiting:
                    self._rate_control_limiting = True
            if self._rate_control_limiting and not force:
                self._rate_control_discard_count += 1
                self._logger.warning("discarding data due to rate-limiting: %s", data)
                return
        try:
            line_data = "%s\r\n" % data
            self.push(line_data.encode('utf-8', errors='ignore'))
            self._logger.debug("-> %s", line_data.strip())
        except BaseException as be:
            self._logger.error("error while sending data: %s" % be)

    def _handle_channel_join(self, msg):
        self._logger.info("joined %s" % (msg['target']))
        self._joined_channels.append(msg['target'])

    def _handle_server_message(self, msg):
        if msg['action'] == 'NICKINUSE':
            nick = user_set_or_default('HonkMaster3', 'nick', self._irc_settings)
            rand_from_nick = "%s-%s" % (nick, random.randint(0, 100))
            altnick = user_set_or_default(rand_from_nick, 'altnick', self._irc_settings)
            self._encsendline("NICK %s" % altnick)
        if msg['action'] == 'ENDOFMOTD':
            self._selected_nick = msg['target']
            self._queue_channel_joins()
        if msg['action'] == 'JOIN' and _get_nick_from_source(msg['source']) == self._selected_nick:
            self._handle_channel_join(msg)
            self._ready = True
        if msg['action'] == 'PRIVMSG' and len(self._message_handlers) > 0:
            for handler in self._message_handlers:
                handler(msg)

    def _parse_server_message(self, msg):
        if msg.startswith('PING'):
            challenge = msg.split(':')[1].strip()
            self._encsendline('PONG :%s' % challenge, True)
            self._logger.info("ping %s? pong %s!", challenge, challenge)
            return
        rest = None
        try:
            source, action, target, rest = msg.split(' ', 3)
            source = source.strip()
            action = action.strip()
            target = target.strip()
            rest = rest.strip()
        except Exception:
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
                action = 'UNK%s' % action
        self._handle_server_message({'source': source, 'action': action, 'target': target, 'data': rest})

    def register_message_handler(self, fn):
        self._message_handlers.append(fn)

    def broadcast_message(self, msg):
        if not self._ready:
            self._logger.debug("defer message until ready: %s", msg)
        while not self._ready:
            time.sleep(1)
        for channel in self._joined_channels:
            self._send_message_to_channel(channel, msg)

    def collect_incoming_data(self, data):
        incoming = data.decode('utf-8', errors='ignore')
        self._rbuf.write(incoming)

    def found_terminator(self):
        msg = self._rbuf.getvalue()
        self._rbuf.truncate(0)
        self._rbuf.seek(0)
        try:
            msg_decoded = msg
            self._logger.debug("<- %s", msg_decoded.strip())
            self._parse_server_message(msg_decoded)
        except BaseException as be:
            self._logger.exception(be)
            self._logger.error("failed to parse line from server: %s", msg)
