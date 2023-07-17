from model_tools import get_vectorizer_model
from sys import argv
from tools import read_mail, read_email
from constants import TEXT_MODEL, TEXT_VECTORIZER


def predict_mail(*_file_names: str):

    file_names: list[str] = []
    contents: list[str] = []

    for file_name in _file_names:
        content = read_mail(file_name)
        if content is not None:
            file_names.append(file_name)
            contents.append(content)

    vectorizer, model = get_vectorizer_model(
        model_type=TEXT_MODEL, vectorizer_type=TEXT_VECTORIZER)

    features_predict = vectorizer.transform(contents)
    # prediction_values = model.predict_proba(features_predict)
    predictions = model.predict(features_predict)
    prediction_values = predictions

    for i, file_name in enumerate(file_names):
        print(predictions[i], prediction_values[i],
              f"predicted for {file_name}")


if __name__ == '__main__':
    if argv:
        predict_mail(*argv[1:])
