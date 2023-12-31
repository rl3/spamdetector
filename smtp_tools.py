import itertools
import os
import re
import smtplib
import socket
from email import policy
from email.parser import BytesParser
from functools import reduce
from sqlite3 import OperationalError
from typing import AnyStr

from aiosmtpd.handlers import CRLF, EMPTYBYTES, NLCRE
from aiosmtpd.smtp import SMTP, Envelope, Session

from ai_filter_daemon import AIFilterDaemon
from config import (MAIL_HEADER_FIELD_PREFIX, RE_RECIPIENTS_FILTER,
                    SUBJECT_PREFIX)
from constants import NEXT_PEER_PORT_DEFAULT, SMTP_ERROR_CODE_554
from mail_logging import LOG_DEBUG, LOG_ERROR, LOG_INFO
from mail_logging.logging import log
from tools import convert_message

# Create a custom SMTP class by subclassing smtplib.SMTP


class UnixSocketSMTP(smtplib.SMTP):
    """
    Subclass of smtplib.SMTP to bind on unix socket
    """

    def _get_socket(self, host: str, port: int, timeout: float):
        s = socket.socket(socket.AF_UNIX)
        s.connect(host)
        return s


class AISpamFrowarding:
    def __init__(self, filter_daemon: AIFilterDaemon, next_peer: str):
        self.filter_daemon = filter_daemon
        self.next_peer = next_peer

    async def handle_DATA(self, server: SMTP, session: Session, envelope: Envelope):
        recipients: list[str] = [
            str(rcpt) for rcpt in envelope.rcpt_tos  # type:ignore
        ]

        log(LOG_INFO, f'Parsing mail for {", ".join(recipients)}')

        # Get the original message
        _original_message = envelope.content
        if _original_message is None:
            return "500 Empty message"

        original_message = (
            _original_message.encode(encoding="utf-8", errors='ignore')
            if isinstance(_original_message, str)
            else _original_message
        )

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

        # Determine for wich recipients we should perform spam detection
        skip_recipients: list[str] = []
        apply_recipients: list[str] = []
        for recipient in recipients:
            if recipient_applies(recipient):
                apply_recipients.append(recipient)
            else:
                skip_recipients.append(recipient)

        skip_refused: dict[str, tuple[int, bytes]] = {}
        apply_refused: dict[str, tuple[int, bytes]] = {}

        async def pass_message_unchanged(recipients: list[str]):
            return await self._handle_DATA(
                server=server,
                session=session,
                mail_from=str(envelope.mail_from),
                rcpt_tos=recipients,
                content=original_message
            )

        # Pass mail unchanged for skip_recipients
        if skip_recipients:
            log(
                LOG_DEBUG,
                f'Skip spam detection for recipients {", ".join(skip_recipients)}'
            )
            skip_refused = await pass_message_unchanged(skip_recipients)

        # Run spam detection for apply_recipients
        if apply_recipients:

            # Create a new message to modify
            parser = BytesParser(policy=policy.default)
            parsed_message = convert_message(
                parser.parsebytes(original_message)
            )
            # modified_message = EmailMessage(policy=policy.default)
            # modified_message.set_content(original_message)

            try:
                prediction, label = self.filter_daemon.predict_mail(
                    parsed_message
                )

                if prediction and SUBJECT_PREFIX is not None:
                    # Modify the subject
                    old_subject = str(parsed_message.get('Subject') or '')
                    parsed_message.replace_header(
                        'Subject',
                        f"{SUBJECT_PREFIX} {old_subject}"
                    )

                # Add custom headers
                parsed_message.add_header(
                    f'{MAIL_HEADER_FIELD_PREFIX.decode()}-Result', label
                )

                log(
                    LOG_DEBUG,
                    f'Spam detection result {label} for recipients {", ".join(apply_recipients)}'
                )

                # Forward the modified message
                apply_refused = await self._handle_DATA(
                    server=server,
                    session=session,
                    mail_from=str(envelope.mail_from),
                    rcpt_tos=apply_recipients,
                    content=parsed_message.as_bytes()
                )

            except OperationalError as error:
                log(LOG_ERROR, str(error))
                log(LOG_INFO, "Passing mail untested.")
                apply_refused = await pass_message_unchanged(apply_recipients)

        refused = {**skip_refused, **apply_refused}

        if refused:
            return smtplib.CRLF.join(
                itertools.chain(
                    (f'{SMTP_ERROR_CODE_554}-Delivery to the following recipients failed:',),
                    (
                        f'{SMTP_ERROR_CODE_554}-{recipient}: {error_code} {error_message.decode(encoding="utf-8", errors="ignore")}'
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
            peer = (
                session.peer.encode("ascii") or b'unix-socket'
                if isinstance(session.peer, str)
                else session.peer[0].encode("ascii")
            )
            lines.insert(_i, MAIL_HEADER_FIELD_PREFIX +
                         b"-Peer: " + peer + ending)

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
            smtp: smtplib.SMTP
            if self.next_peer.find('/') >= 0:
                log(
                    LOG_DEBUG,
                    f"Trying to send mail to next hop via unix:{self.next_peer}"
                )
                smtp = UnixSocketSMTP(os.path.abspath(self.next_peer))
            else:
                smtp = smtplib.SMTP()

                socket_data = self.next_peer.split(sep=':', maxsplit=1)
                hostname: str = socket_data[0]
                port: int = (
                    int(socket_data[1])
                    if len(socket_data) > 1
                    else NEXT_PEER_PORT_DEFAULT
                )
                log(
                    LOG_DEBUG,
                    f"Trying to send mail to next hop via smtp:{hostname}:{port}"
                )
                smtp.connect(hostname, port)

            try:
                refused = smtp.sendmail(mail_from, rcpt_tos, data)  # pytype: disable=wrong-arg-types  # noqa: E501
                log(
                    LOG_DEBUG,
                    f"Refused error: {refused}"
                )
            finally:
                smtp.quit()
        except smtplib.SMTPRecipientsRefused as e:  # pylint:disable=invalid-name
            refused = e.recipients
            log(
                LOG_ERROR,
                f"SMTPRecipientsRefused: {e}"
            )
        except (OSError, smtplib.SMTPException) as e:  # pylint:disable=invalid-name
            log(
                LOG_ERROR,
                f"SMTPException: {e}"
            )
            # All recipients were refused.  If the exception had an associated
            # error code, use it.  Otherwise, fake it with a non-triggering
            # exception code.
            errcode = getattr(e, "smtp_code", -1)
            errmsg = getattr(e, "smtp_error", b"ignore")
            for r in rcpt_tos:
                refused[str(r)] = (errcode, errmsg)

        return refused
