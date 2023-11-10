#!./start

import argparse
import asyncio
import grp
import os
import pwd
import re

from aiosmtpd.controller import Controller, UnixSocketController

from ai_filter_daemon import AIFilterDaemon
from config import (LISTENING_SOCKET_DATA, LOG_FILE, LOG_LEVEL,
                    NEXT_PEER_SOCKET_DATA)
from constants import SERVER_PORT_DEFAULT
from mail_logging import LOG_ERROR, LOG_INFO
from mail_logging.logging import init_logger, log
from smtp_tools import AISpamFrowarding


class AIFilterMailDaemon:
    def __init__(
        self,
        listen_socket: str,
        next_peer: str,
        uid: int,
        gid: int,
    ) -> None:
        init_logger(LOG_FILE, LOG_LEVEL)

        self.filter_daemon = AIFilterDaemon()
        self.listen_socket = listen_socket
        self.next_peer = next_peer
        self.runas_uid = uid
        self.runas_gid = gid
        self.is_unix_socket = self.listen_socket.find('/') >= 0

    def drop_privileges(self):
        if os.getuid() != 0:
            return

        log(LOG_INFO,
            f"Dropping privileges to uid {self.runas_uid}/gid {self.runas_gid}")

        os.setgroups([])

        os.setuid(self.runas_uid)
        os.setgid(self.runas_gid)

    def _get_unix_controller(self, handler: AISpamFrowarding):
        if os.path.exists(self.listen_socket):
            log(
                LOG_ERROR,
                f'Socket {self.listen_socket} already exists. Exiting'
            )
            exit(3)

        socket_dir = os.path.dirname(self.listen_socket)
        os.makedirs(
            name=socket_dir,
            exist_ok=True
        )
        try:
            os.chown(socket_dir, self.runas_uid, self.runas_gid)
        except:  # pylint:disable=bare-except
            pass

        self.drop_privileges()

        log(
            LOG_INFO,
            f'Starting smtp server listening on socket {self.listen_socket}'
        )
        return UnixSocketController(handler=handler, unix_socket=os.path.abspath(self.listen_socket))

    def _get_ip_controller(self, handler: AISpamFrowarding):
        socket_data = self.listen_socket.split(sep=':', maxsplit=1)
        hostname: str = socket_data[0]
        port: int = (
            int(socket_data[1])
            if len(socket_data) > 1
            else SERVER_PORT_DEFAULT
        )

        self.drop_privileges()

        log(
            LOG_INFO,
            f'Starting smtp server listening on {hostname}:{port}'
        )
        return Controller(handler=handler, hostname=hostname, port=port)

    def get_controller(self):
        handler = AISpamFrowarding(
            filter_daemon=self.filter_daemon,
            next_peer=self.next_peer
        )
        if self.is_unix_socket >= 0:
            return self._get_unix_controller(handler)

        return self._get_ip_controller(handler)

    def run(self):

        async def start_server(loop: asyncio.AbstractEventLoop) -> None:  # pylint:disable=unused-argument,redefined-outer-name
            controller = self.get_controller()
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
            if self.is_unix_socket and os.path.exists(self.listen_socket):
                os.remove(self.listen_socket)


def parse_args_and_start():
    parser = argparse.ArgumentParser(
        description="Mailer daemon to detect spam mails"
    )
    parser.add_argument(
        '-s', '--socket',
        dest='socket',
        default=LISTENING_SOCKET_DATA,
        help='The socket to wait for connections on. If it contains a slash it\'s treated as a unix socket else as a hostname/address with optional port separated by a colon.',
    )
    parser.add_argument(
        '-n', '--next-hop',
        dest='next_peer',
        default=NEXT_PEER_SOCKET_DATA,
        help='The socket to write parsed mails to. If it contains a slash it\'s treated as a unix socket else as a hostname/address with optional port separated by a colon.',
    )
    parser.add_argument(
        '-p', '--pid',
        dest='pid_file',
        help='The PID file.',
    )
    parser.add_argument(
        '-u', '--user',
        dest='user',
        help='The user to run this process as.',
    )
    parser.add_argument(
        '-g', '--group',
        dest='group',
        help='The group to run this process as.',
    )

    args = parser.parse_args()

    pid_file_name: str | None = args.pid_file
    listen_socket: str = args.socket
    next_peer: str = args.next_peer
    runas_user: str = args.user or '0'
    runas_group: str = args.group or '0'
    runas_uid: int = (
        int(runas_user)
        if re.fullmatch(r'\d+', runas_user)
        else pwd.getpwnam(runas_user).pw_uid
    )
    runas_gid: int = (
        int(runas_group)
        if re.fullmatch(r'\d+', runas_group)
        else grp.getgrnam(runas_group).gr_gid
    )

    if pid_file_name is not None:
        with open(file=args.pid_file, mode='w', encoding='UTF-8') as pid_file:
            pid_file.write(str(os.getpid()))

    AIFilterMailDaemon(
        listen_socket=listen_socket,
        next_peer=next_peer,
        uid=runas_uid,
        gid=runas_gid,
    ).run()

    if pid_file_name is not None and os.path.isfile(pid_file_name):
        os.unlink(pid_file_name)


if __name__ == "__main__":
    parse_args_and_start()
