import threading
import logging


def run_plugin(plugin, chat_client):
    handle = PluginRunner(plugin, chat_client)
    handle.start()
    return handle


class PluginRunner(threading.Thread):
    def __init__(self, plugin, chat_client):
        threading.Thread.__init__(self)
        self._logger = logging.getLogger('pr-%s' % plugin.__name__)
        self._plugin = plugin
        self._chat_client = chat_client
        self._crashed = False
        self._finished = False
        self.daemon = True

        message_handler = getattr(self._plugin, 'handle_message', None)
        if message_handler is not None:
            self._chat_client.register_message_handler(message_handler)

    def run(self):
        self._logger.debug("now listening for new messages")
        try:
            for msg in self._plugin.get_messages():
                self._chat_client.broadcast_message(msg)
        except BaseException as be:
            self._logger.exception(be)
            self._crashed = True
        self._finished = True
