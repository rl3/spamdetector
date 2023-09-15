import asyncio
import itertools
import os
import re
import signal
import smtplib
import socket
import threading
from email import policy
from email.message import EmailMessage
from email.parser import BytesParser
from functools import reduce
from types import FrameType
from typing import AnyStr

from aiosmtpd.controller import Controller, UnixSocketController
from aiosmtpd.handlers import CRLF, EMPTYBYTES, NLCRE
from aiosmtpd.smtp import SMTP, Envelope, Session

from config import (RE_RECIPIENTS_FILTER, RECEIVING_SOCKET_DATA,
                    SENDING_SOCKET_DATA, SUBJECT_PREFIX)
from constants import LOG_INFO, SERVER_PORT_DEFAULT, SMTP_ERROR_CODE_554
from mail_logging import log
from spam_detector import SpamDetector
from tools import convert_message, read_mail

# pylint: disable=pointless-string-statement
'''
class AISpamSMTPServer(SMTP):
    async def handle_DATA(self):
        pass

    async def process_message(self, peer, mailfrom, rcpttos, data, **kwargs):
        # Implement your mail filtering logic here
        # Access the email content through the `data` parameter
        # Return `None` to accept the email or an error message to reject it
        return None  # Accept all emails


class AISpamControllerMixin(BaseThreadedController):
    def factory(self):
        return AISpamSMTPServer(self.handler)


class AISpamController(AISpamControllerMixin, Controller):
    pass


class AISpamUnixController(AISpamControllerMixin, UnixSocketController):
    pass
'''


class AIFilterDaemon:
    def __init__(self) -> None:
        self._spam_detector: SpamDetector | None = None
        self.lock = threading.RLock()
        self._original_hup_handler = signal.getsignal(signal.SIGHUP)

        def handle_sighup(_signum: int, _frame: FrameType | None):
            if self._spam_detector is None:
                log(LOG_INFO, "Not yet initialized. Do nothing.")
                return

            log(LOG_INFO, "Reloading model...")
            self._spam_detector.reload()
            log(LOG_INFO, "Done reloading model.")

        signal.signal(signal.SIGHUP, handler=handle_sighup)

    def __del__(self):
        signal.signal(signal.SIGHUP, handler=self._original_hup_handler)

    def _get_spam_detector(self):
        with self.lock:
            if self._spam_detector is not None:
                return self._spam_detector

            self._spam_detector = SpamDetector()
            return self._spam_detector

    def predict_mail(self, mail_body: EmailMessage) -> tuple[bool, str]:
        prediction = self._get_spam_detector().predict_mail(
            content=read_mail(message=mail_body)
        )

        result = "SPAM" if prediction else "HAM"

        log(LOG_INFO, f"Parsing finished with classification {result}")

        return (prediction, result)


FILTER_DAEMON = AIFilterDaemon()

# Create a custom SMTP class by subclassing smtplib.SMTP


class UnixSocketSMTP(smtplib.SMTP):
    def _get_socket(self, host: str, port: int, timeout: float):
        s = socket.socket(socket.AF_UNIX)
        s.connect(host)
        return s


class AISpamFrowarding:
    def __init__(self):
        self._hostname = SENDING_SOCKET_DATA
        self._port = 0

    async def handle_DATA(self, server: SMTP, session: Session, envelope: Envelope):
        recipients: list[str] = [
            str(rcpt) for rcpt in envelope.rcpt_tos  # type:ignore
        ]

        # Get the original message
        original_message = envelope.content
        if original_message is None:
            return "500 Empty message"

        if isinstance(original_message, str):
            original_message = original_message.encode(encoding="utf-8")

        def recipient_applies(recipient: str) -> bool:
            return reduce(
                (
                    lambda apply, re_tuple:
                    re_tuple[1]
                    if re.match(pattern=re_tuple[0], string=recipient, flags=re.IGNORECASE)
                    else apply
                ),
                RE_RECIPIENTS_FILTER,
                True
            )

        log(LOG_INFO, f'Parsing mail for {recipients}')

        skip_recipients: list[str] = []
        apply_recipients: list[str] = []
        for recipient in recipients:
            if recipient_applies(recipient):
                apply_recipients.append(recipient)
            else:
                skip_recipients.append(recipient)

        skip_refused: dict[str, tuple[int, bytes]] = {}
        apply_refused: dict[str, tuple[int, bytes]] = {}

        if skip_recipients:
            skip_refused = await self._handle_DATA(
                server=server,
                session=session,
                mail_from=str(envelope.mail_from),
                rcpt_tos=skip_recipients,
                content=original_message
            )

        if apply_recipients:
            # Create a new message to modify
            parser = BytesParser(policy=policy.default)
            modified_message = convert_message(
                parser.parsebytes(original_message)
            )
            # modified_message = EmailMessage(policy=policy.default)
            # modified_message.set_content(original_message)

            prediction, label = FILTER_DAEMON.predict_mail(modified_message)

            if prediction and SUBJECT_PREFIX is not None:
                # Modify the subject
                old_subject = str(modified_message.get('Subject') or '')
                modified_message.replace_header(
                    'Subject',
                    f"{SUBJECT_PREFIX} {old_subject}"
                )

            # Add custom headers
            modified_message.add_header('RL3-AI-Spam-Filter', label)

            # Forward the modified message
            apply_refused = await self._handle_DATA(
                server=server,
                session=session,
                mail_from=str(envelope.mail_from),
                rcpt_tos=apply_recipients,
                content=modified_message.as_bytes()
            )

        refused = {**skip_refused, **apply_refused}

        if refused:
            return smtplib.CRLF.join(
                itertools.chain(
                    (f'{SMTP_ERROR_CODE_554}-Delivery to the following recipients failed:',),
                    (
                        f'{SMTP_ERROR_CODE_554}-{recipient}: {error_code} {error_message.decode(encoding="utf-8")}'
                        for recipient, (error_code, error_message) in refused.items()
                    ),
                    (f'{SMTP_ERROR_CODE_554} OK', '')
                )
            )

        return "250 OK"

    async def _handle_DATA(
        self, server: SMTP, session: Session, mail_from: str, rcpt_tos: list[str], content: bytes  # pylint: disable=unused-argument
    ):
        """
        Adapted from aiosmtpd.handler.Proxy to return correct result

        Returns:
            _type_: list of errors and failed recipients
        """
        lines = content.splitlines(keepends=True)
        # Look for the last header
        _i = 0
        ending = CRLF
        for _i, line in enumerate(lines):  # pragma: nobranch
            if NLCRE.match(line):
                ending = line
                break
        if session.peer is not None:
            peer = session.peer[0].encode("ascii")
            lines.insert(_i, b"RL3-AI-Spam-Filter-Peer: " + peer + ending)

        data = EMPTYBYTES.join(lines)
        refused = self._deliver(mail_from, rcpt_tos, data)
        # TBD: what to do with refused addresses?
        return refused

    def _deliver(
        self, mail_from: str, rcpt_tos: list[str], data: AnyStr
    ):
        """
        Adapted from aiosmtpd.handler.Proxy to support unix sockets as receiving mail server

        Returns:
            _type_: _description_
        """
        refused: dict[str, tuple[int, bytes]] = {}
        try:
            s: smtplib.SMTP
            if SENDING_SOCKET_DATA.find('/') >= 0:
                s = UnixSocketSMTP(os.path.abspath(SENDING_SOCKET_DATA))
            else:
                s = smtplib.SMTP()

                socket_data = self._hostname.split(sep=':', maxsplit=1)
                hostname: str = socket_data[0]
                port: int = int(socket_data[1]) if len(
                    socket_data) > 1 else self._port
                s.connect(hostname, port)

            try:
                refused = s.sendmail(mail_from, rcpt_tos, data)  # pytype: disable=wrong-arg-types  # noqa: E501
            finally:
                s.quit()
        except smtplib.SMTPRecipientsRefused as e:  # pylint:disable=invalid-name
            refused = e.recipients
        except (OSError, smtplib.SMTPException) as e:  # pylint:disable=invalid-name
            # All recipients were refused.  If the exception had an associated
            # error code, use it.  Otherwise, fake it with a non-triggering
            # exception code.
            errcode = getattr(e, "smtp_code", -1)
            errmsg = getattr(e, "smtp_error", b"ignore")
            for r in rcpt_tos:
                refused[str(r)] = (errcode, errmsg)

        return refused


if __name__ == "__main__":

    def get_controller():
        handler = AISpamFrowarding()
        if RECEIVING_SOCKET_DATA[0] == socket.AF_UNIX:
            assert (isinstance(RECEIVING_SOCKET_DATA[1], str))
            return UnixSocketController(handler=handler, unix_socket=RECEIVING_SOCKET_DATA[1])
            # return AISpamUnixController(AISpamFrowarding(), unix_socket=RECEIVING_SOCKET_DATA[1])
        else:
            hostname: str
            port: int = SERVER_PORT_DEFAULT
            if isinstance(RECEIVING_SOCKET_DATA[1], str):
                hostname = RECEIVING_SOCKET_DATA[1]
            else:
                hostname, port = RECEIVING_SOCKET_DATA[1]

            return Controller(handler=handler, hostname=hostname, port=port)
            # return AISpamController(handler=Sink(), hostname=hostname, port=port)

    async def start_server(loop: asyncio.AbstractEventLoop) -> None:  # pylint:disable=unused-argument,redefined-outer-name
        controller = get_controller()
        controller.start()

    loop: asyncio.AbstractEventLoop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop=loop)
    loop.create_task(start_server(loop=loop))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        print("User abort indicated")
