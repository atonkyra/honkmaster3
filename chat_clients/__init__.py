import glob
import importlib
import logging
import sys

from os.path import dirname, basename


def add_chat_client(target, name, chat_client):
    target[name] = chat_client


logger = logging.getLogger('chat-clients')
available_chat_clients = {}
candidate_chat_clients = glob.glob(dirname(__file__)+'/*.py')
for chat_client in candidate_chat_clients:
    chat_client_module_name = basename(chat_client).split('.')[0]
    if chat_client_module_name in ['__init__']:
        continue
    try:
        importlib.import_module('chat_clients.%s' % chat_client_module_name)
        add_chat_client(
            available_chat_clients,
            chat_client_module_name,
            sys.modules["chat_clients.%s" % chat_client_module_name].__chat_client_class__
        )
        logger.info('imported chat-client %s', chat_client_module_name)
    except BaseException as be:
        logger.error('chat-client load failed: %s', be)
