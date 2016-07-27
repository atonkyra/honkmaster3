import threading
import logging


def run_plugin(plugin, irc_client):
    handle = PluginRunner(plugin, irc_client)
    handle.start()
    return handle


class PluginRunner(threading.Thread):
    def __init__(self, plugin, irc_client):
        threading.Thread.__init__(self)
        self._logger = logging.getLogger('pr-%s' % (plugin.__name__))
        self._plugin = plugin
        self._irc_client = irc_client
        self._crashed = False
        self._finished = False
        self.daemon = True

    def run(self):
        self._logger.debug("now listening for new messages")
        try:
            for msg in self._plugin.get_messages():
                self._irc_client.broadcast_message(msg)
        except BaseException as be:
            self._crashed = True
        self._finished = True
