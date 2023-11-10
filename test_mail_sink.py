#!./start

import asyncio
import os
import re

from aiosmtpd.controller import Controller, UnixSocketController
from aiosmtpd.handlers import Sink
from aiosmtpd.smtp import SMTP, Envelope, Session

from config import MAIL_HEADER_FIELD_PREFIX, NEXT_PEER_SOCKET_DATA
from constants import SERVER_PORT_DEFAULT


class TestProxy(Sink):
    async def handle_DATA(self, server: SMTP, session: Session, envelope: Envelope):  # pylint: disable=unused-argument
        re_header_fields = (
            r'(?<=\n)\s*(' +
            re.escape(MAIL_HEADER_FIELD_PREFIX.decode()) +
            r'[\-\w]+:.*\S)(?=\s*\n)'
        )
        print(f"Receiving mail for {envelope.rcpt_tos}")  # type:ignore
        content = envelope.content
        if content is not None:
            if isinstance(content, bytes):
                content = content.decode(encoding="utf-8", errors='ignore')
            print(content)
            if matches := re.findall(re_header_fields, content):
                print("*" * 80)
                for match in matches:
                    print(match)
            print("*" * 80)
        return "250 OK"


if __name__ == "__main__":

    def _get_controller():
        handler = TestProxy()
        if NEXT_PEER_SOCKET_DATA.find('/') >= 0:
            if os.path.isfile(NEXT_PEER_SOCKET_DATA):
                print(
                    f'Socket {NEXT_PEER_SOCKET_DATA} already exists. Exiting')
                exit(3)
            print(
                f'Starting smtp server listening on socket {NEXT_PEER_SOCKET_DATA}')
            return UnixSocketController(handler=handler, unix_socket=os.path.abspath(NEXT_PEER_SOCKET_DATA))
            # return AISpamUnixController(AISpamFrowarding(), unix_socket=RECEIVING_SOCKET_DATA[1])
        else:
            socket_data = NEXT_PEER_SOCKET_DATA.split(sep=':', maxsplit=1)
            hostname: str = socket_data[0]
            port: int = int(socket_data[1]) if len(
                socket_data) > 1 else SERVER_PORT_DEFAULT

            print(f'Starting smtp server listening on {hostname}:{port}')
            return Controller(handler=handler, hostname=hostname, port=port)

    async def _start_server(loop: asyncio.AbstractEventLoop) -> None:  # pylint:disable=unused-argument,redefined-outer-name
        controller = _get_controller()
        controller.start()

    loop: asyncio.AbstractEventLoop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop=loop)
    loop.create_task(_start_server(loop=loop))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        print("User abort indicated")
        if NEXT_PEER_SOCKET_DATA.find('/') >= 0 and os.path.isfile(NEXT_PEER_SOCKET_DATA):
            os.remove(NEXT_PEER_SOCKET_DATA)
