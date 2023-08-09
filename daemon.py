import os
import signal
import socket
import threading
from types import FrameType

from constants import SOCKET_DATA
from spam_detector import SpamDetector
from tools import read_mail_from_str

MAIL_TEST = SpamDetector()


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

    # Send the modified mail back to Postfix
    connection.sendall((add_header + mail_body).encode('utf-8'))
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
            target=handle_mail, args=(connection,))
        client_thread.start()
        # handle_mail(connection)


if __name__ == '__main__':

    # pylint: disable=unidiomatic-typecheck
    if SOCKET_DATA[0] == socket.AF_UNIX and type(SOCKET_DATA[1]) == str and os.path.isfile(SOCKET_DATA[1]):
        print(f"Socket {SOCKET_DATA[1]} already exists. Exiting.")
        exit(1)

    try:
        start_filter()
    finally:
        if SOCKET_DATA[0] == socket.AF_UNIX and type(SOCKET_DATA[1]) == str:
            os.unlink(SOCKET_DATA[1])
