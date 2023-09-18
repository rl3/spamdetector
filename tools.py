
import os
import re
from email import policy
from email.message import EmailMessage, Message
from email.parser import BytesParser

import chardet
from html2text import html2text

from config import RE_SPAM_SUBJECT_PREFIX
from constants import MAX_SIZE, MailContent
from mail_logging import LOG_ERROR
from mail_logging.logging import log


def fix_re_tuples(res: list[tuple[str, re.RegexFlag] | str]):
    return tuple(
        re_
        if isinstance(re_, tuple)
        else (re_, re.IGNORECASE)
        for re_ in res
    )


def detect_encoding(file_path: str):
    with open(file_path, 'rb') as file:
        raw_data = file.read(MAX_SIZE + 10)
        result = chardet.detect(raw_data)
        return result['encoding']


def valid_file_name(file_name: str) -> bool:
    base_name = os.path.basename(file_name)
    return True if re.fullmatch(r'\d+\.', base_name) or re.search(r'\.eml$', base_name) or base_name.endswith('.txt') else False


def convert_message(message: EmailMessage | Message) -> EmailMessage:
    if isinstance(message, EmailMessage):
        return message

    email_message = EmailMessage(policy=policy.default)
    for key in message.keys():
        email_message[key] = message[key]
    email_message.set_content(message.get_payload())
    return email_message


def read_mail_from_file(file_name: str) -> MailContent | None:
    if valid_file_name(file_name):
        parser = BytesParser(policy=policy.default)
        with open(file_name, 'rb') as fh:
            message = convert_message(parser.parse(fh))

        return read_mail(message)
    return None


def read_mail_from_str(mail_body: str) -> MailContent:
    parser = BytesParser(policy=policy.default)
    message = convert_message(parser.parsebytes(mail_body.encode('utf-8')))

    return read_mail(message)


def read_mail(message: EmailMessage) -> MailContent:

    email_from = str(message.get_unixfrom() or message['From'] or '')
    if match := re.search(r'[\w\.-]+@[\w\.-]+(?:\.[\w]+)+', email_from):
        email_from = match[0]

    email_subject = str(message['Subject'] or '')
    for re_tuple in fix_re_tuples(RE_SPAM_SUBJECT_PREFIX):
        email_subject = re.sub(
            re_tuple[0], repl='', string=email_subject, flags=re_tuple[1])

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
            log(LOG_ERROR, message.get_content_type())
            log(LOG_ERROR, message.get_charsets())
            return None

        if email_body is not None and message.get_content_type() == 'text/html':
            return html2text(email_body)
        return email_body

    email_body = _get_body(message) or ''

    return (f"FROM: {email_from}", f"SUBJECT: {email_subject}", email_body)


if __name__ == '__main__':
    mail = read_mail_from_file('mails/stephan/Spam/636.')
    print(mail)
