import asyncio
import os

from aiosmtpd.controller import Controller, UnixSocketController
from aiosmtpd.handlers import Sink
from aiosmtpd.smtp import SMTP, Envelope, Session

from config import SENDING_SOCKET_DATA
from constants import SERVER_PORT_DEFAULT


class TestProxy(Sink):
    async def handle_DATA(self, server: SMTP, session: Session, envelope: Envelope):  # pylint: disable=unused-argument
        print(f"Receiving mail for {envelope.rcpt_tos}")  # type:ignore
        content = envelope.content
        if isinstance(content, bytes):
            content = content.decode(encoding="utf-8")
        print(content)
        return "250 OK"


if __name__ == "__main__":

    def _get_controller():
        handler = TestProxy()
        if SENDING_SOCKET_DATA.find('/') >= 0:
            return UnixSocketController(handler=handler, unix_socket=os.path.abspath(SENDING_SOCKET_DATA))
            # return AISpamUnixController(AISpamFrowarding(), unix_socket=RECEIVING_SOCKET_DATA[1])
        else:
            socket_data = SENDING_SOCKET_DATA.split(sep=':', maxsplit=1)
            hostname: str = socket_data[0]
            port: int = int(socket_data[1]) if len(
                socket_data) > 1 else SERVER_PORT_DEFAULT

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
