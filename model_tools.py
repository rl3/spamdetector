
from constants import MODEL_FILE_PREFIX, MODEL_FILE_EXT, VOCABULARY_FILE_PREFIX, VOCABULARY_FILE_EXT, TEXT_TRANSFORMER, TEXT_MODEL, NEW_MODEL
import os
import pickle
from typing import Union
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer  # type: ignore
from sklearn.naive_bayes import MultinomialNB  # type: ignore
from sklearn.svm import SVC  # type: ignore

ModelType = Union[SVC, MultinomialNB]
VectorizerType = Union[CountVectorizer, TfidfVectorizer]


def _get_model_file_name() -> str:
    return f"{MODEL_FILE_PREFIX}-{TEXT_MODEL}-{TEXT_TRANSFORMER}{MODEL_FILE_EXT}"


def _get_vectorizer_file_name() -> str:
    return f"{VOCABULARY_FILE_PREFIX}-{TEXT_TRANSFORMER}{VOCABULARY_FILE_EXT}"


def _load_model() -> ModelType | None:
    file_name = _get_model_file_name()
    try:
        if os.path.isfile(file_name) and os.access(file_name, os.R_OK):
            with open(file_name, 'rb') as file_handle:
                print(f"Loding model from file '{file_name}'")
                return pickle.load(file_handle)
    except:
        print(f"Loding model from file '{file_name}' failed")
    return None


def _new_model() -> ModelType:
    if TEXT_MODEL == 'MultinomialNB':
        return MultinomialNB()

    return SVC(probability=True)


def _load_vectorizer() -> VectorizerType | None:
    try:
        file_name = _get_vectorizer_file_name()
        if os.path.isfile(file_name) and os.access(file_name, os.R_OK):
            with open(file_name, 'rb') as file_handle:
                print(f"Loading vectorizer from file '{file_name}'")
                return pickle.load(file_handle)
    except:
        print(f"Loading vectorizer from file '{file_name}' failed")
    return None


def _new_vectorizer() -> VectorizerType:
    if TEXT_TRANSFORMER == 'TfidfVectorizer':
        return TfidfVectorizer()

    return CountVectorizer()


def get_vectorizer_model(train: bool = False) -> tuple[VectorizerType, ModelType]:
    vectorizer = _load_vectorizer()
    if vectorizer is None:
        if train:
            return (_new_vectorizer(), _new_model())
        raise Exception("Could not load vectorizer")

    model = _load_model()
    if model is None:
        if train:
            return (vectorizer, _new_model())
        raise Exception("Could not load model")

    return (vectorizer, model)


def _save_model(model: ModelType):
    file_name = _get_model_file_name()
    with open(file_name, 'wb') as file_handle:
        pickle.dump(model, file_handle)


def _save_vectorizer(transformer: VectorizerType):
    file_name = _get_vectorizer_file_name()

    with open(file_name, 'wb') as file_handle:
        pickle.dump(transformer, file_handle)


def save_vectorizer_model(model: ModelType, transformer: VectorizerType):
    _save_model(model)
    _save_vectorizer(transformer)
