import socket
import ssl


def establish_connection(addr, port, logger, enable_ssl=False):
    gai = socket.getaddrinfo(addr, port)
    for gaddr in gai:
        family = gaddr[0]
        real_addr = gaddr[-1][0]
        real_port = gaddr[-1][1]
        if family == socket.AF_INET or family == socket.AF_INET6:
            try:
                logger.info("establishing connection to %s:%s (%s)", addr, port, real_addr)
                skt = socket.socket(family, socket.SOCK_STREAM)
                if enable_ssl:
                    ctx = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
                    skt = ctx.wrap_socket(skt)
                skt.settimeout(5)
                skt.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
                try:
                    skt.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 5)
                    skt.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 20)
                    skt.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 6)
                except Exception:
                    pass
                skt.connect((real_addr, real_port))
                logger.info("connected")
                return skt
            except BaseException as be:
                logger.error(be)
    return None

