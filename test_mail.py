from sys import argv

from config_model import SpamDetectorModel
from tools import read_mail_from_file


def predict_mail(*_file_names: str):

    spam_detector = SpamDetectorModel(for_training=False)
    predictions: list[bool] = []

    for file_name in _file_names:
        content = read_mail_from_file(file_name)
        if content is not None:
            predictions.append(spam_detector.predict_mail(content=content))

    for i, file_name in enumerate(_file_names):
        print(predictions[i], f"predicted for {file_name}")


if __name__ == '__main__':
    if argv:
        predict_mail(*argv[1:])
