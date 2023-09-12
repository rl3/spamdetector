import os
import re
import signal
import socket
import threading
from types import FrameType

from constants import SOCKET_DATA, SUBJECT_PREFIX
from spam_detector import SpamDetector
from tools import read_mail_from_str

MAIL_TEST = SpamDetector()

'''
What should a postfix mail filter output and return when called?
ANSWER | GPT-3.5 MODEL
When a postfix mail filter is called, it should output a modified version of the original email message and return an
exit status code to indicate the result of the filtering process. The output and return values depend on the specific
requirements and logic of the filter. Here are some common scenarios:

- Accept the email: If the filter determines that the email should be accepted and delivered, it should output the
  original email message without any modifications and return an exit status code of 0.
- Reject the email: If the filter determines that the email should be rejected and not delivered, it should output
  an error message indicating the reason for rejection and return a non-zero exit status code. The specific error
  message and exit status code can vary depending on the reason for rejection.
- Modify the email: If the filter needs to modify the email before delivering it, it should output the modified version
  of the email message and return an exit status code of 0. The modifications can include adding or removing headers,
  changing the message body, or altering any other part of the email.

It's important to note that the exact implementation of the postfix mail filter and the specific output and return values
may vary depending on the programming language and framework being used. The above scenarios provide a general guideline,
but you should refer to the documentation or examples specific to your chosen implementation to ensure proper integration
with postfix.
'''


def handle_sighup(_signum: int, _frame: FrameType | None):
    print("Reloading model...")
    MAIL_TEST.reload()
    print("Done reloading model")


signal.signal(signal.SIGHUP, handler=handle_sighup)


def handle_mail(connection: socket.socket):
    mail_body: str = ''
    while True:
        data = connection.recv(1024)
        if not data:
            break
        mail_body += data.decode('utf-8')
    prediction = MAIL_TEST.predict_mail(read_mail_from_str(mail_body))

    result = "SPAM" if prediction else "HAM"

    print("Finished", result)

    add_header = f'RL3-AI-Spam-Filter: {result}\r\n'
    new_mail_body = (
        re.sub(
            pattern=r'^Subject:\s+',
            repl=f'Subject: {SUBJECT_PREFIX} ',
            string=mail_body,
            flags=re.MULTILINE | re.IGNORECASE,
            count=1
        )
        if prediction and SUBJECT_PREFIX
        else mail_body
    )

    # Send the modified mail back to Postfix
    connection.sendall((add_header + new_mail_body).encode('utf-8'))
    connection.close()


def start_filter():
    server_socket = socket.socket(
        family=SOCKET_DATA[0], type=socket.SOCK_STREAM)
    server_socket.bind(SOCKET_DATA[1])
    server_socket.listen(10)

    print(f'Listening on {SOCKET_DATA[1]} with PID {os.getpid()}')

    while True:
        connection, _address = server_socket.accept()
        client_thread = threading.Thread(
            target=handle_mail, args=(connection,)
        )
        client_thread.start()
        # handle_mail(connection)


if __name__ == '__main__':

    address_family, address = SOCKET_DATA

    if address_family == socket.AF_UNIX and isinstance(address, str) and os.path.isfile(address):
        print(f"Socket {address} already exists. Exiting.")
        exit(1)

    try:
        start_filter()
    finally:
        if address_family == socket.AF_UNIX and isinstance(address, str):
            os.unlink(address)
