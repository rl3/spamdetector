
import os
import re
import sys
import time
from random import shuffle
from typing import Callable, NamedTuple

from config import (DEFAULT_SPAM_LEARN_DIRS, LAST_LEARN_SEMAPHORE,
                    RE_IGNORE_PATH, RE_SPAM_PATH)
from config_model import SpamDetectorModel
from constants import TRAIN_CHUNK_SIZE
from mail_logging import LOG_DEBUG, LOG_INFO
from mail_logging.logging import log
from mail_types import MailContent
from spam_detector_model_base import SpamDetectorModelBase
from tools import fix_re_tuples, read_mail_from_file, valid_file_name

label_files: list[tuple[str, str]] = []


class OptionsType(NamedTuple):
    not_before: float | None = None


def __scope1() -> tuple[Callable[[str], str], Callable[[str], bool]]:
    _re_spam_path = fix_re_tuples(RE_SPAM_PATH)

    def __get_label(path: str) -> str:
        for regexp, flags in _re_spam_path:
            if re.search(regexp, path, flags=flags):
                return "spam"
        return "ham"

    _re_ignore_path = fix_re_tuples(RE_IGNORE_PATH)

    def __ignore_path(path: str) -> bool:
        for regexp, flags in _re_ignore_path:
            if re.search(regexp, path, flags=flags):
                return True
        return False

    return __get_label, __ignore_path


_get_label, _ignore_path = __scope1()


def add_files(root_path: str, rel_path: str, options: OptionsType):
    ignore_file = _ignore_path(rel_path)

    label: str = _get_label(rel_path)
    print(rel_path, label, f'ignore: {ignore_file}')

    for file in os.listdir(os.path.join(root_path, rel_path)):
        rel_file_path = os.path.normpath(os.path.join(rel_path, file))
        full_file_path = os.path.join(root_path, rel_file_path)
        if os.path.isdir(full_file_path):
            if options.not_before is not None and os.stat(full_file_path).st_mtime < options.not_before:
                continue

            add_files(
                root_path=root_path,
                rel_path=rel_file_path,
                options=options
            )
            continue

        if ignore_file:
            continue

        if valid_file_name(rel_file_path):
            label_files.append((label, full_file_path))
        else:
            log(LOG_DEBUG, f"Skipping {label} file {full_file_path}")


def train(path: str, spam_model: SpamDetectorModelBase, options: OptionsType):
    log(LOG_INFO, f"Loading mails from '{path}'")
    add_files(root_path=path, rel_path='', options=options)

    log(LOG_INFO, f"Training {len(label_files)} mails...")

    shuffle(label_files)

    def _train(round_no: int):
        start = round_no * TRAIN_CHUNK_SIZE
        end = start + TRAIN_CHUNK_SIZE

        mail_contents: list[MailContent] = []
        labels: list[str] = []

        log(LOG_DEBUG, f"Reading files (round {round_no + 1})")
        for label, file_name in label_files[start:end]:
            mail_content = read_mail_from_file(file_name)
            if mail_content is not None:
                mail_contents.append(mail_content)
                labels.append(label)

        spam_model.learn_mails(contents=mail_contents, labels=labels)

    round_no = 0
    while round_no * TRAIN_CHUNK_SIZE < len(label_files):
        _train(round_no)
        round_no += 1


def train_all(*pathes: str, options: OptionsType | None):
    if options is None:
        options = OptionsType()
    spam_detector_model: SpamDetectorModelBase = SpamDetectorModel(
        for_training=True
    )
    for path in pathes:
        train(path=path, spam_model=spam_detector_model, options=options)
    spam_detector_model.save_model()


if __name__ == '__main__':
    dirs: list[str] = DEFAULT_SPAM_LEARN_DIRS
    if len(sys.argv) > 1:
        dirs = [dir for dir in sys.argv[1:] if os.path.isdir(dir)]

    start_time = time.time()

    not_before: float | None = None
    if os.path.isfile(LAST_LEARN_SEMAPHORE):
        stats = os.stat(LAST_LEARN_SEMAPHORE)
        not_before = stats.st_mtime

    train_all(*dirs, options=OptionsType(
        not_before=not_before
    ))

    try:
        with open(file=LAST_LEARN_SEMAPHORE, mode="a"):  # pylint: disable=unspecified-encoding
            os.utime(path=LAST_LEARN_SEMAPHORE, times=(start_time, start_time))
    except:  # pylint: disable=bare-except
        pass
