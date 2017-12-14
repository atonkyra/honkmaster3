#!/usr/bin/env python3
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)-15s %(levelname)-8s %(name)-18s %(message)s'
)
logger = logging.getLogger('honkmaster3')
import sys
import logging
from lib.pluginrunner import run_plugin
import argparse
import chat_clients
import plugins
from lib.multiordereddict import MultiOrderedDict
import configparser

cckeys = chat_clients.available_chat_clients.keys()
parser = argparse.ArgumentParser(description='HonkMaster3 Relay Bot', add_help=False)
parser.add_argument('relaytype', metavar='relaytype', choices=cckeys)
type_args, unknown_args = parser.parse_known_args()

parser = argparse.ArgumentParser(description='HonkMaster3 IRC Bot', add_help=False)
parser.add_argument('-c', '--config', required=True, help='Include config from file', default=None)
config_args, unknown_args = parser.parse_known_args(unknown_args)

iniconf = configparser.RawConfigParser(dict_type=MultiOrderedDict, strict=False, empty_lines_in_values=False)
iniconf.read(config_args.config)

def start_plugins(chat_client, config):
    if 'plugin' not in config['honkmaster3']:
        return
    for plugin in config['honkmaster3']['plugin']:
        plugin_args = None
        if ':' in plugin:
            plugin, plugin_args = plugin.split(':', 1)
        if plugin in plugins.available_plugins:
            if plugin_args is None:
                p = plugins.available_plugins[plugin]()
            else:
                p = plugins.available_plugins[plugin](plugin_args)
            run_plugin(p, chat_client)
        else:
            logger.error("plugin not found: %s", plugin)


def run_honkmaster(skt):
    irc_settings = build_irc_settings()
    irc_client = lib.ircclient.IRCClient(skt, **irc_settings)
    start_plugins(irc_client)
    asyncore.loop(timeout=0.1)


def main():
    chat_client = chat_clients.available_chat_clients[type_args.relaytype](iniconf[type_args.relaytype])
    start_plugins(chat_client, iniconf)
    chat_client.run()

if __name__ == "__main__":
    main()
