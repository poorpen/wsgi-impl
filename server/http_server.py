import socket
import logging
import selectors

from typing import Callable
from functools import partial

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


class HTTPServer:

    @staticmethod
    def _bing_server_socket() -> socket.socket:
        _socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        _socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return _socket

    def __init__(self):
        self._selector = selectors.DefaultSelector()
        self._server_socket = self._bing_server_socket()

    def _read_connections(self, conn, callback: Callable):
        data = conn.recv(4096)
        if data:
            result = callback(data)
            conn.sendall(result.encode())
        conn.close()
        self._selector.unregister(conn)

    def _accept_connections(self, sock, callback: Callable):
        conn, addr = sock.accept()
        logger.info(f'Accepted connection from {addr}')
        conn.setblocking(False)
        self._selector.register(conn, selectors.EVENT_READ, partial(self._read_connections, callback=callback))

    def bind(self, host: str, port: int) -> None:
        self._server_socket.bind((host, port))
        logger.info(f" Running on http://{host}:{port} (Press CTRL+C to quit)")

    def run(self, callback: Callable):
        self._server_socket.listen()
        self._server_socket.setblocking(False)
        self._selector.register(
            self._server_socket, selectors.EVENT_READ, partial(self._accept_connections, callback=callback)
        )
        logger.info(f" Listening...")
        while True:
            events = self._selector.select(1)
            for key, _ in events:
                callback = key.data
                callback(key.fileobj)