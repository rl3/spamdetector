
from sklearn.model_selection import train_test_split  # type: ignore
import os
from constants import HAM_DIR, SPAM_DIR, MAX_SIZE, LIMIT_FILES, TEST_SIZE
from model_tools import get_model, save_model, get_transformer, save_transformer
from tools import read_mail
from random import shuffle

from glob import glob


label_bodies: list[tuple[str, str]] = []


def add_files(dir: str, label: str):
    count = len([l for l in label_bodies if l == label])
    for file_name in glob(f"{dir}/*"):
        if LIMIT_FILES is not None and count > LIMIT_FILES:
            return count

        if os.path.isdir(file_name):
            count += add_files(file_name, label)
            continue

        content = read_mail(file_name)
        if content:
            label_bodies.append((label, content))
            count += 1
        else:
            print(f"Skipping {label} file", file_name)

    return count


print("Loading SPAM")
add_files(SPAM_DIR, label='spam')

print("Lodaing HAM")
add_files(HAM_DIR, label='ham')

if TEST_SIZE:
    print("Splitting data")
    bodies_train, bodies_test, labels_train, labels_test = train_test_split(
        [lb[1] for lb in label_bodies],
        [lb[0] for lb in label_bodies],
        test_size=TEST_SIZE
    )
else:
    shuffle(label_bodies)
    bodies_train = [lb[1] for lb in label_bodies]
    labels_train = [lb[0] for lb in label_bodies]
    bodies_test = []
    labels_test = []

print("Transforming train data")
transormer = get_transformer()
features = transormer.fit_transform(bodies_train)

model = get_model(train=True)
print("Learning...")
model.fit(features, labels_train)

if TEST_SIZE:
    print("Transforming test data")
    features_test = transormer.transform(bodies_test)

    print("Scoring...")
    print(model.score(features_test, labels_test))

save_model(model)
save_transformer(transormer)
