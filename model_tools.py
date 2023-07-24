
import os
import pickle
from typing import Iterable, Union

from sklearn.feature_extraction.text import CountVectorizer  # type: ignore
from sklearn.feature_extraction.text import TfidfVectorizer  # type: ignore
from sklearn.feature_extraction.text import _VectorizerMixin  # type: ignore
from sklearn.naive_bayes import MultinomialNB  # type: ignore
from sklearn.svm import SVC  # type: ignore

from constants import (MODEL_FILE_EXT, MODEL_FILE_PREFIX, VECTORIZER_FILE_EXT,
                       VOCABULARY_FILE_PREFIX)

ModelType = Union[SVC, MultinomialNB]
VectorizerType = Union[CountVectorizer, TfidfVectorizer]


def _get_model_file_name(model_type: type, vectorizer_type: type) -> str:
    return f"{MODEL_FILE_PREFIX}-{model_type.__name__}-{vectorizer_type.__name__}{MODEL_FILE_EXT}"


def _get_vectorizer_file_name(vectorizer_type: type) -> str:
    return f"{VOCABULARY_FILE_PREFIX}-{vectorizer_type.__name__}{VECTORIZER_FILE_EXT}"


def _load_model(model_type: type, vectorizer_type: type) -> ModelType | None:
    file_name = _get_model_file_name(
        model_type=model_type, vectorizer_type=vectorizer_type)
    try:
        if os.path.isfile(file_name) and os.access(file_name, os.R_OK):
            with open(file_name, 'rb') as file_handle:
                print(f"Loding model from file '{file_name}'")
                model = pickle.load(file_handle)
                if isinstance(model, model_type):
                    return model
                print(
                    f"Object in file '{file_name}' has wrong type. Expected '{model_type.__name__}' got '{type(model).__name__}'")
    except:  # pylint: disable=bare-except
        print(f"Loding model from file '{file_name}' failed")
    return None


def _load_vocabulary(vectorizer_type: type) -> dict[str, int]:
    file_name = _get_vectorizer_file_name(vectorizer_type=vectorizer_type)
    try:
        if os.path.isfile(file_name) and os.access(file_name, os.R_OK):
            with open(file_name, 'rb') as file_handle:
                print(f"Loading vectorizer from file '{file_name}'")
                vocabulary = pickle.load(file_handle)
                return vocabulary

    except:  # pylint: disable=bare-except
        print(f"Loading vectorizer from file '{file_name}' failed")
    return {}


def get_vectorizer(vectorizer_type: type, vocabulary: dict[str, int]):
    return vectorizer_type(ngram_range=(1, 3), strip_accents='unicode', decode_error='ignore', vocabulary=vocabulary)


def get_vocabulary_model(vectorizer_type: type, model_type: type, train: bool = False) -> tuple[dict[str, int], ModelType]:
    vocabulary = _load_vocabulary(vectorizer_type=vectorizer_type)
    if len(vocabulary) == 0:
        if train:
            return (vocabulary, model_type())
        raise Exception(  # pylint: disable=broad-exception-raised
            "Could not load vectorizer")

    model = _load_model(model_type=model_type, vectorizer_type=vectorizer_type)
    if model is None:
        if train:
            return (vocabulary, model_type())
        raise Exception(  # pylint: disable=broad-exception-raised
            "Could not load model")

    return (vocabulary, model)


def save_vocabulary_model(vocabulary: dict[str, int], vectorizer_type: type, model: ModelType):
    with open(_get_model_file_name(model_type=type(model), vectorizer_type=vectorizer_type), 'wb') as file_handle:
        pickle.dump(model, file_handle)
    with open(_get_vectorizer_file_name(vectorizer_type=vectorizer_type), 'wb') as file_handle:
        pickle.dump(vocabulary, file_handle)


def extend_vocabulary(documents: Iterable[str], vocabulary: dict[str, int], vectorizer: _VectorizerMixin):
    analyze = vectorizer.build_analyzer()  # type:ignore
    for doc in documents:
        for feature in analyze(doc):  # type: ignore
            feature = str(feature).lower() # type: ignore
            if feature not in vocabulary:
                vocabulary[feature] = vocabulary.__len__()  # type: ignore
