#!./start

import os
import smtplib
import sys

from config import LISTENING_SOCKET_DATA
from constants import SERVER_PORT_DEFAULT
from smtp_tools import UnixSocketSMTP

if __name__ == '__main__':

    if len(sys.argv) <= 2:
        print(f"Usage: {sys.argv[0]} [mail from] [rcpt to]... < mail_to_parse")
        exit(1)

    assert (len(sys.argv) > 2)
    mail_from = sys.argv[1]
    rcpt_tos = sys.argv[2:]

    print(f"Trying to send mail from {mail_from} to {rcpt_tos}")

    body = b''
    while True:
        data = sys.stdin.buffer.read(1024)
        if not data:
            break
        body += data

    refused = {}
    try:
        s: smtplib.SMTP
        if LISTENING_SOCKET_DATA.find('/') >= 0:
            print(f"Sending mail to socket {LISTENING_SOCKET_DATA}")
            s = UnixSocketSMTP(os.path.abspath(LISTENING_SOCKET_DATA))
        else:
            s = smtplib.SMTP()

            socket_data = LISTENING_SOCKET_DATA.split(sep=':', maxsplit=1)
            hostname: str = socket_data[0]
            port: int = int(socket_data[1]) if len(
                socket_data) > 1 else SERVER_PORT_DEFAULT
            print(f"Sending mail to {hostname} port {port}")
            s.connect(hostname, port)

        try:
            refused = s.sendmail(mail_from, rcpt_tos, body)  # pytype: disable=wrong-arg-types  # noqa: E501
        finally:
            s.quit()
    except smtplib.SMTPRecipientsRefused as e:
        print("got SMTPRecipientsRefused")
        refused = e.recipients
    except (OSError, smtplib.SMTPException) as e:
        print("got %s", e.__class__)
        # All recipients were refused.  If the exception had an associated
        # error code, use it.  Otherwise, fake it with a non-triggering
        # exception code.
        errcode = getattr(e, "smtp_code", -1)
        errmsg = getattr(e, "smtp_error", b"ignore")
        for r in rcpt_tos:
            refused[r] = (errcode, errmsg)
    print(refused)
