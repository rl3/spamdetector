import itertools
import os
import re
import smtplib
import socket
from email import policy
from email.parser import BytesParser
from functools import reduce
from typing import AnyStr

from aiosmtpd.handlers import CRLF, EMPTYBYTES, NLCRE
from aiosmtpd.smtp import SMTP, Envelope, Session

from ai_filter_daemon import AIFilterDaemon
from config import DEFAULT_NEXT_PEER_PORT, RE_RECIPIENTS_FILTER, SUBJECT_PREFIX
from constants import SMTP_ERROR_CODE_554
from mail_logging import LOG_INFO
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

        log(LOG_INFO, f'Parsing mail for {", ".join(recipients)}')

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

            prediction, label = self.filter_daemon.predict_mail(
                modified_message)

            if prediction and SUBJECT_PREFIX is not None:
                # Modify the subject
                old_subject = str(modified_message.get('Subject') or '')
                modified_message.replace_header(
                    'Subject',
                    f"{SUBJECT_PREFIX} {old_subject}"
                )

            # Add custom headers
            modified_message.add_header('RL3-AI-Spam-Filter-Result', label)

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
            peer = (
                session.peer.encode("ascii") or b'unix-socket'
                if isinstance(session.peer, str)
                else session.peer[0].encode("ascii")
            )
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
            smtp: smtplib.SMTP
            if self.next_peer.find('/') >= 0:
                smtp = UnixSocketSMTP(os.path.abspath(self.next_peer))
            else:
                smtp = smtplib.SMTP()

                socket_data = self.next_peer.split(sep=':', maxsplit=1)
                hostname: str = socket_data[0]
                port: int = (
                    int(socket_data[1])
                    if len(socket_data) > 1
                    else DEFAULT_NEXT_PEER_PORT
                )
                smtp.connect(hostname, port)

            try:
                refused = smtp.sendmail(mail_from, rcpt_tos, data)  # pytype: disable=wrong-arg-types  # noqa: E501
            finally:
                smtp.quit()
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
