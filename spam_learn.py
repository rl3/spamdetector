
from sklearn.model_selection import train_test_split  # type: ignore
import os
from constants import HAM_DIR, SPAM_DIR, TRAIN_CHUNK_SIZE
from model_tools import _save_model, get_vectorizer_model, _save_vectorizer
from tools import read_mail, valid_file_name
from random import shuffle

from glob import glob


label_files: list[tuple[str, str]] = []


def add_files(dir: str, label: str):
    for file_name in glob(f"{dir}/*"):
        if os.path.isdir(file_name):
            add_files(file_name, label)
            continue

        if valid_file_name(file_name):
            label_files.append((label, file_name))
        else:
            print(f"Skipping {label} file", file_name)


print("Loading SPAM")
add_files(SPAM_DIR, label='spam')

print("Lodaing HAM")
add_files(HAM_DIR, label='ham')

file_names_test: list[str] = []
label_names_test: list[str] = []

shuffle(label_files)

vectorizer, model = get_vectorizer_model(train=True)


def train(round: int):
    start = round * TRAIN_CHUNK_SIZE
    end = start + TRAIN_CHUNK_SIZE

    bodies: list[str] = []
    labels: list[str] = []
    print(f"Reading files (round {round + 1})")
    for label, file_name in label_files[start:end]:
        body = read_mail(file_name)
        if body is not None:
            bodies.append(body)
            labels.append(label)

    print(f"Transforming train data (round {round + 1})")
    features = vectorizer.fit_transform(bodies)

    print(f"Learning (round {round + 1})")
    model.fit(features, labels)


round = 0
while round * TRAIN_CHUNK_SIZE < len(label_files):
    train(round)
    round += 1

_save_model(model)
_save_vectorizer(vectorizer)
