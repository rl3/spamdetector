from model_tools import get_model, get_transformer
from sys import argv
from tools import read_mail


def predict_mail(*_file_names: str):

    file_names: list[str] = []
    contents: list[str] = []

    for file_name in _file_names:
        content = read_mail(file_name)
        if content is not None:
            file_names.append(file_name)
            contents.append(content)

    model = get_model()
    transformer = get_transformer()

    features_predict = transformer.transform(contents)
    predictions = model.predict_proba(features_predict)

    for i, file_name in enumerate(file_names):
        print(predictions[i], f"predicted for {file_name}")


if __name__ == '__main__':
    if argv:
        predict_mail(*argv[1:])
