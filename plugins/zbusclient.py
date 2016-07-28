import os
import threading
import time
import logging
import zmq
import json
import sys


logger = logging.getLogger('zbusclient')


class ZBusClient(object):
    __name__ = "zbusclient"

    def __init__(self, sarg):
        args = sarg.split(';')
        if len(args) != 3:
            logger.error("zbusclient requires arguments like zmq-address;topic;formatstring, supplied: %s", sarg)
            sys.exit(1)
        source = args[0]
        subscribe = args[1]
        self._fmtstring = args[2]
        self._ctx = zmq.Context()
        self._skt = self._ctx.socket(zmq.SUB)
        self._skt.set(zmq.SUBSCRIBE, subscribe.encode('ascii', errors='ignore'))
        self._skt.connect(source)

    def get_messages(self):
        while True:
            try:
                topic, data = self._skt.recv_multipart()
                logger.debug("new data: topic=%s data=%s", topic, data)
                inc_data = json.loads(data)
                inc_data['topic'] = topic
                string = self._fmtstring.format(**inc_data)
                yield string
            except BaseException as be:
                logger.exception(be)


__plugin_class__ = ZBusClient
