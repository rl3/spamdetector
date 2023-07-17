
from constants import MODEL_FILE_PREFIX, MODEL_FILE_EXT, VECTORIZER_FILE_PREFIX, VECTORIZER_FILE_EXT, TEXT_VECTORIZER, TEXT_MODEL, NEW_MODEL
import os
import pickle
from typing import Union
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer  # type: ignore
from sklearn.naive_bayes import MultinomialNB  # type: ignore
from sklearn.svm import SVC  # type: ignore

ModelType = Union[SVC, MultinomialNB]
VectorizerType = Union[CountVectorizer, TfidfVectorizer]


def _get_model_file_name(model_type: type, vectorizer_type: type) -> str:
    return f"{MODEL_FILE_PREFIX}-{model_type.__name__}-{vectorizer_type.__name__}{MODEL_FILE_EXT}"


def _get_vectorizer_file_name(vectorizer_type: type) -> str:
    return f"{VECTORIZER_FILE_PREFIX}-{vectorizer_type.__name__}{VECTORIZER_FILE_EXT}"


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
    except:
        print(f"Loding model from file '{file_name}' failed")
    return None


def _load_vectorizer(vectorizer_type: type) -> VectorizerType | None:
    try:
        file_name = _get_vectorizer_file_name(vectorizer_type=vectorizer_type)
        if os.path.isfile(file_name) and os.access(file_name, os.R_OK):
            with open(file_name, 'rb') as file_handle:
                print(f"Loading vectorizer from file '{file_name}'")
                vectorizer = pickle.load(file_handle)
                if isinstance(vectorizer, vectorizer_type):
                    return vectorizer
                print(
                    f"Object in file '{file_name}' has wrong type. Expected '{vectorizer_type.__name__}' got '{type(vectorizer).__name__}'")

    except:
        print(f"Loading vectorizer from file '{file_name}' failed")
    return None


def get_vectorizer_model(vectorizer_type: type, model_type: type, train: bool = False) -> tuple[VectorizerType, ModelType]:
    vectorizer = _load_vectorizer(vectorizer_type=vectorizer_type)
    if vectorizer is None:
        if train:
            return (vectorizer_type(), model_type())
        raise Exception("Could not load vectorizer")

    model = _load_model(model_type=model_type, vectorizer_type=vectorizer_type)
    if model is None:
        if train:
            return (vectorizer, model_type())
        raise Exception("Could not load model")

    return (vectorizer, model)


def save_vectorizer_model(vectorizer: VectorizerType, model: ModelType):
    with open(_get_model_file_name(model_type=type(model), vectorizer_type=type(vectorizer)), 'wb') as file_handle:
        pickle.dump(model, file_handle)
    with open(_get_vectorizer_file_name(vectorizer_type=type(vectorizer)), 'wb') as file_handle:
        pickle.dump(vectorizer, file_handle)
