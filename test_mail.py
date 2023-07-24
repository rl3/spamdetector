from sys import argv

from numpy import vectorize

from constants import TEXT_MODEL, TEXT_VECTORIZER
from model_tools import get_vectorizer, get_vocabulary_model
from tools import read_mail


def predict_mail(*_file_names: str):

    file_names: list[str] = []
    froms: list[str] = []
    subjects: list[str] = []
    bodies: list[str] = []

    for file_name in _file_names:
        content = read_mail(file_name)
        if content is not None:
            _from, subject, body = content

            file_names.append(file_name)
            froms.append(_from)
            subjects.append(subject)
            bodies.append(body or '')

    vocabulary, model = get_vocabulary_model(
        model_type=TEXT_MODEL, vectorizer_type=TEXT_VECTORIZER)
    vectorizer = get_vectorizer(TEXT_VECTORIZER, vocabulary)

    features_predict = (
        vectorizer.fit_transform(froms)
        + vectorizer.fit_transform(subjects)
        + vectorizer.fit_transform(bodies)
    )
    # prediction_values = model.predict_proba(features_predict)
    predictions = model.predict(features_predict)
    prediction_values = predictions

    for i, file_name in enumerate(file_names):
        print(predictions[i], prediction_values[i],
              f"predicted for {file_name}")


if __name__ == '__main__':
    if argv:
        predict_mail(*argv[1:])
