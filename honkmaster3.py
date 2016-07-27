#!/usr/bin/env python
import asyncore
import socket
import logging
import lib.ircclient
from lib.pluginrunner import run_plugin
import argparse
import ssl


logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)-15s %(levelname)-8s %(name)-18s %(message)s'
)
logger = logging.getLogger('honkmaster3')
parser = argparse.ArgumentParser(description='HonkMaster3 IRC Bot')
parser.add_argument('-s', '--server', required=True, help='IRC server to join')
parser.add_argument('--server-password', required=False, help='IRC server password', default=None)
parser.add_argument('-P', '--port', required=False, help='IRC server port', default=6667, type=int)
parser.add_argument('-S', '--ssl', required=False, help='use SSL', default=False, action='store_true')
parser.add_argument('-c', '--channel', required=True, help='IRC channels to join, may be specified multiple times', action='append', default=[])
parser.add_argument('-n', '--nick', required=False, help='IRC nick')
parser.add_argument('-r', '--realname', required=False, help='IRC realname')
parser.add_argument('-p', '--plugin', required=False, help='Plugins to use, argument by plugin:arg1, may be specified multiple times', action='append', default=[])
args = parser.parse_args()
import plugins


def establish_connection(addr, port):
    gai = socket.getaddrinfo(addr, port)
    for gaddr in gai:
        family = gaddr[0]
        real_addr = gaddr[-1][0]
        real_port = gaddr[-1][1]
        if family == socket.AF_INET or family == socket.AF_INET6:
            try:
                logger.info("establishing connection to %s:%s (%s)", addr, port, real_addr)
                skt = socket.socket(family, socket.SOCK_STREAM)
                if args.ssl:
                    ctx = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
                    skt = ctx.wrap_socket(skt)
                skt.settimeout(5)
                skt.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
                try:
                    skt.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 5)
                    skt.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 20)
                    skt.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 6)
                except:
                    pass
                skt.connect((addr, port))
                logger.info("connected")
                return skt
            except BaseException as be:
                logger.error(be)
    return None


def start_plugins(irc_client):
    for plugin in args.plugin:
        plugargs = None
        if ':' in plugin:
            plugin, plugargs = plugin.split(':',1)
        p = None
        if plugin in plugins.available_plugins:
            if plugargs is None:
                p = plugins.available_plugins[plugin]()
            else:
                p = plugins.available_plugins[plugin](plugargs)
            run_plugin(p, irc_client)
        else:
            logger.error("plugin not found: %s", plugin)


def build_irc_settings():
    irc_settings = {}
    if args.server_password is not None:
        irc_settings['server_password'] = args.server_password
    irc_settings['channels'] = args.channel
    if args.nick is not None:
        irc_settings['nick'] = args.nick
    if args.realname is not None:
        irc_settings['realname'] = args.realname
    return irc_settings


def run_honkmaster(skt):
    irc_settings = build_irc_settings()
    irc_client = lib.ircclient.IRCClient(skt, **irc_settings)
    start_plugins(irc_client)
    asyncore.loop(timeout=0.1)


def main():
    skt = establish_connection(args.server, args.port)
    if skt is not None:
        run_honkmaster(skt)


if __name__ == "__main__":
    main()
