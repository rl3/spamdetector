import re
import socket
import sys

from config import RE_RECIPIENTS_TO_APPLY, RE_RECIPIENTS_TO_IGNORE, SOCKET_DATA
from daemon import handle_mail
from spam_detector import SpamDetector


def pass_through():
    for line in sys.stdin:
        sys.stdout.write(line)

    exit(0)


def pass_to_socket():
    sock = socket.socket(SOCKET_DATA[0], socket.SOCK_STREAM)

    try:
        sock.connect(SOCKET_DATA[1])
    except socket.error:
        direct_call()

    while True:
        data = sys.stdin.buffer.read(1024)
        if not data:
            break
        sock.sendall(data)

    sock.shutdown(socket.SHUT_WR)

    while True:
        data = sock.recv(1024)
        if not data:
            break
        sys.stdout.buffer.write(data)

    sock.close()

    exit(0)


def direct_call():
    mail_body: str = ''
    while True:
        data = sys.stdin.buffer.read(1024)
        if not data:
            break
        mail_body += data.decode('utf-8')

    spam_detector = SpamDetector()

    _prediction, _result, new_mail_body = handle_mail(
        mail_body=mail_body,
        mail_detector=spam_detector
    )

    sys.stdout.buffer.write(new_mail_body)

    exit(0)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(f"Usage: {__file__} [recipient]")
        exit(1)
    recipient = sys.argv[1]

    apply: bool = False if RE_RECIPIENTS_TO_APPLY else True

    for re_apply in RE_RECIPIENTS_TO_APPLY:
        if re.match(re_apply, recipient):
            apply = True

    for re_ignore in RE_RECIPIENTS_TO_IGNORE:
        if re.match(re_ignore, recipient):
            apply = False

    if not apply:
        pass_through()

    pass_to_socket()
