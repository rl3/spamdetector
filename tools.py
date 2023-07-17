
import chardet
from constants import MAX_SIZE
import os
import re


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
