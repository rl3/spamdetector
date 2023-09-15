import smtplib
import sys

from config import RECEIVING_SOCKET_DATA

if __name__ == '__main__':
    assert (len(sys.argv) > 2)
    mail_from = sys.argv[1]
    rcpt_tos = sys.argv[2:]

    body = b''
    while True:
        data = sys.stdin.buffer.read(1024)
        if not data:
            break
        body += data

    assert (isinstance(RECEIVING_SOCKET_DATA[1], tuple))

    refused = {}
    try:
        s = smtplib.SMTP()
        s.connect(RECEIVING_SOCKET_DATA[1][0], RECEIVING_SOCKET_DATA[1][1])
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
