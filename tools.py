
import os
import re
from email import policy
from email.message import EmailMessage, Message
from email.parser import BytesParser

import chardet
from html2text import html2text

from constants import MAX_SIZE


def detect_encoding(file_path: str):
    with open(file_path, 'rb') as file:
        raw_data = file.read(MAX_SIZE + 10)
        result = chardet.detect(raw_data)
        return result['encoding']


def valid_file_name(file_name: str) -> bool:
    base_name = os.path.basename(file_name)
    return True if re.fullmatch(r'\d+\.', base_name) or re.search(r'\.eml$', base_name) else False


def convert_message(message: EmailMessage | Message) -> EmailMessage:
    if isinstance(message, EmailMessage):
        return message

    email_message = EmailMessage(policy=policy.default)
    for key in message.keys():
        email_message[key] = message[key]
    email_message.set_content(message.get_payload())
    return email_message


def read_mail(file_name: str) -> tuple[str, str, str] | None:
    if valid_file_name(file_name):
        parser = BytesParser(policy=policy.default)
        with open(file_name, 'rb') as fh:
            message = convert_message(parser.parse(fh))

            email_from = message.get_unixfrom() or message['From'] or ''
            if match := re.search(r'[\w\.-]+@[\w\.-]+(?:\.[\w]+)+', email_from):
                email_from = match[0]

            email_subject = message['Subject'] or ''

            def _get_body(message: EmailMessage):
                if message.is_multipart():
                    email_body_message = message.get_body(
                        preferencelist=("html", "plain")
                    )
                    if email_body_message is None:
                        return None

                    message = convert_message(email_body_message)

                try:
                    email_body = message.get_content()
                    email_body = None if email_body is None else str(
                        email_body)
                except:  # pylint: disable=bare-except
                    print(file_name)
                    print(message.get_content_type())
                    print(message.get_charsets())
                    return None

                if email_body is not None and message.get_content_type() == 'text/html':
                    return html2text(email_body)
                return email_body

            email_body = _get_body(message) or ''

            return (f"FROM: {email_from}", f"SUBJECT: {email_subject}", email_body)

    return None


if __name__ == '__main__':
    mail = read_mail('mails/stephan/Spam/636.')
    print(mail)
