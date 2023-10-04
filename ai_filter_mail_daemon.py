#!./start

import asyncio
import os

from aiosmtpd.controller import Controller, UnixSocketController

from ai_filter_daemon import AIFilterDaemon
from config import LISTENING_SOCKET_DATA, LOG_FILE, LOG_LEVEL
from constants import SERVER_PORT_DEFAULT
from mail_logging import LOG_ERROR, LOG_INFO
from mail_logging.logging import init_logger, log
from smtp_tools import AISpamFrowarding

if __name__ == "__main__":

    init_logger(LOG_FILE, LOG_LEVEL)

    FILTER_DAEMON = AIFilterDaemon()

    def get_controller():
        handler = AISpamFrowarding(FILTER_DAEMON)
        if LISTENING_SOCKET_DATA.find('/') >= 0:
            if os.path.isfile(LISTENING_SOCKET_DATA):
                log(
                    LOG_ERROR,
                    f'Socket {LISTENING_SOCKET_DATA} already exists. Exiting'
                )
                exit(3)
            log(
                LOG_INFO,
                f'Starting smtp server listening on socket {LISTENING_SOCKET_DATA}'
            )
            return UnixSocketController(handler=handler, unix_socket=os.path.abspath(LISTENING_SOCKET_DATA))
            # return AISpamUnixController(AISpamFrowarding(), unix_socket=RECEIVING_SOCKET_DATA[1])
        else:
            socket_data = LISTENING_SOCKET_DATA.split(sep=':', maxsplit=1)
            hostname: str = socket_data[0]
            port: int = int(socket_data[1]) if len(
                socket_data) > 1 else SERVER_PORT_DEFAULT

            log(
                LOG_INFO,
                f'Starting smtp server listening on {hostname}:{port}'
            )
            return Controller(handler=handler, hostname=hostname, port=port)
            # return AISpamController(handler=Sink(), hostname=hostname, port=port)

    async def start_server(loop: asyncio.AbstractEventLoop) -> None:  # pylint:disable=unused-argument,redefined-outer-name
        controller = get_controller()
        controller.start()

    loop: asyncio.AbstractEventLoop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop=loop)
    loop.create_task(start_server(loop))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        log(
            LOG_INFO,
            "User abort indicated"
        )
        if LISTENING_SOCKET_DATA.find('/') >= 0 and os.path.isfile(LISTENING_SOCKET_DATA):
            os.remove(LISTENING_SOCKET_DATA)
