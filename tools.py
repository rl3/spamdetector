
import chardet
from constants import MAX_SIZE
import os
import re
from email.parser import BytesParser
from email import policy, message_from_bytes
from email.message import EmailMessage, Message


def detect_encoding(file_path):
    with open(file_path, 'rb') as file:
        raw_data = file.read(MAX_SIZE + 10)
        result = chardet.detect(raw_data)
        return result['encoding']


def valid_file_name(file_name: str) -> bool:
    base_name = os.path.basename(file_name)
    return True if re.fullmatch(r'\d+\.', base_name) or re.search(r'\.eml$', base_name) else False


def read_mail(file_name: str) -> str | None:
    if valid_file_name(file_name):
        with open(file_name, 'rt', encoding=detect_encoding(file_name), errors='ignore') as fh:
            # with open(file_name, 'rt', encoding='ISO-8859-2') as fh:
            return fh.read(MAX_SIZE)
    return None


def convert_message(message: EmailMessage | Message) -> EmailMessage:
    if isinstance(message, EmailMessage):
        return message

    email_message = EmailMessage(policy=policy.default)
    for key in message.keys():
        email_message[key] = message[key]
    email_message.set_content(message.get_payload())
    return email_message


def read_email(file_name: str) -> str | None:
    if valid_file_name(file_name):
        parser = BytesParser(policy=policy.default)
        with open(file_name, 'rb') as fh:
            message = convert_message(parser.parse(fh))
            print('message', type(message))

            email_from = message.get_unixfrom() or message['From']
            email_subject = message['Subject']
            if message.is_multipart():
                email_body = message.get_body(preferencelist=("html", "plain"))
            else:
                email_body = message.get_content()

            if message.is_multipart():
                print('File name', file_name)
                print('From', email_from)
                print('Subject', email_subject)
                print(email_body)
                exit()

    return None
