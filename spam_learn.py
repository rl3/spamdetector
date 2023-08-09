
import os
import re
from random import shuffle
from typing import Callable, Tuple

from constants import MAIL_DIR, RE_SPAM_PATH, TRAIN_CHUNK_SIZE, MailContent
from spam_detector import SpamDetector
from tools import read_mail_from_file, valid_file_name

label_files: list[tuple[str, str]] = []


def __scope1() -> Callable[[str], str]:
    _re_spam_path: Tuple[tuple[str, re.RegexFlag], ...] = tuple(
        re_spam
        if isinstance(re_spam, tuple)
        else (re_spam, re.IGNORECASE)
        for re_spam in RE_SPAM_PATH
    )

    def __get_label(path: str) -> str:
        for regexp, flags in _re_spam_path:
            if re.search(regexp, path, flags=flags):
                return "spam"
        return "ham"

    return __get_label


_get_label = __scope1()


def add_files(path: str):
    label: str = _get_label(path)

    for _file_path in os.listdir(path):
        file_path = os.path.join(path, _file_path)
        if os.path.isdir(file_path):
            add_files(file_path)
            continue

        if valid_file_name(file_path):
            label_files.append((label, file_path))
        else:
            print(f"Skipping {label} file", file_path)


def train(path: str):
    print(f"Loading mails from '{path}'")
    add_files(path)

    print(f"Training {len(label_files)} mails...")

    shuffle(label_files)

    spam_detector: SpamDetector = SpamDetector(train=True)

    def _train(round_no: int):
        start = round_no * TRAIN_CHUNK_SIZE
        end = start + TRAIN_CHUNK_SIZE

        mail_contents: list[MailContent] = []
        labels: list[str] = []

        print(f"Reading files (round {round_no + 1})")
        for label, file_name in label_files[start:end]:
            mail_content = read_mail_from_file(file_name)
            if mail_content is not None:
                mail_contents.append(mail_content)
                labels.append(label)

        spam_detector.learn_mail(contents=mail_contents, labels=labels)

    round_no = 0
    while round_no * TRAIN_CHUNK_SIZE < len(label_files):
        _train(round_no)
        round_no += 1

    spam_detector.save_vocabulary_model()


if __name__ == '__main__':
    train(MAIL_DIR)
