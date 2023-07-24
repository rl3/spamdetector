
import os
import re
from glob import glob
from itertools import chain
from random import shuffle
from typing import Callable, Tuple

from constants import (MAIL_DIR, RE_SPAM_PATH, TEXT_MODEL, TEXT_VECTORIZER,
                       TRAIN_CHUNK_SIZE)
from model_tools import (extend_vocabulary, get_vectorizer,
                         get_vocabulary_model, save_vocabulary_model)
from tools import read_mail, valid_file_name

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

    for file_path in glob(f"{path}/*"):
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

    vocabulary, model = get_vocabulary_model(
        model_type=TEXT_MODEL, vectorizer_type=TEXT_VECTORIZER, train=True)

    vectorizer = get_vectorizer(TEXT_VECTORIZER, vocabulary)

    def _train(round_no: int):
        start = round_no * TRAIN_CHUNK_SIZE
        end = start + TRAIN_CHUNK_SIZE

        froms: list[str] = []
        subjects: list[str] = []
        bodies: list[str] = []
        labels: list[str] = []
        print(f"Reading files (round {round_no + 1})")
        for label, file_name in label_files[start:end]:
            mail_content = read_mail(file_name)
            if mail_content is not None:
                _from, subject, body = mail_content
                froms.append(_from)
                subjects.append(subject)
                bodies.append(body or '')
                labels.append(label)

        print(f"Extending dictionary (round {round_no + 1})")
        extend_vocabulary(
            documents=chain.from_iterable((froms, subjects, bodies)),
            vocabulary=vocabulary,
            vectorizer=vectorizer
        )

        print(f"Transforming train data (round {round_no + 1})")
        features = (
            vectorizer.fit_transform(froms)  # type: ignore
            + vectorizer.fit_transform(subjects)  # type: ignore
            + vectorizer.fit_transform(bodies)  # type: ignore
        )

        print(f"Learning (round {round_no + 1})")
        model.fit(features, labels)  # type:ignore

    round_no = 0
    while round_no * TRAIN_CHUNK_SIZE < len(label_files):
        _train(round_no)
        round_no += 1

    save_vocabulary_model(
        vocabulary=vocabulary,
        vectorizer_type=type(vectorizer),
        model=model
    )


if __name__ == '__main__':
    train(MAIL_DIR)
