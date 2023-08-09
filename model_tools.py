
import os
import pickle
from typing import Iterable, Type, TypeVar, Union

from sklearn.feature_extraction.text import CountVectorizer  # type: ignore
from sklearn.feature_extraction.text import TfidfVectorizer  # type: ignore
from sklearn.feature_extraction.text import _VectorizerMixin  # type: ignore
from sklearn.naive_bayes import MultinomialNB  # type: ignore
from sklearn.svm import SVC  # type: ignore

from constants import (MODEL_FILE_EXT, MODEL_FILE_PREFIX, N_GRAMS,
                       VECTORIZER_FILE_EXT, VOCABULARY_FILE_PREFIX)

ModelType = Union[SVC, MultinomialNB]
VectorizerType = Union[CountVectorizer, TfidfVectorizer]
VectorizerTypeType = TypeVar(
    "VectorizerTypeType", CountVectorizer, TfidfVectorizer)


def _get_model_file_name(model_type: Type[ModelType], vectorizer_type: Type[VectorizerType]) -> str:
    return f"{MODEL_FILE_PREFIX}-{model_type.__name__}-{vectorizer_type.__name__}{MODEL_FILE_EXT}"


def _get_vectorizer_file_name(vectorizer_type: Type[VectorizerType]) -> str:
    return f"{VOCABULARY_FILE_PREFIX}-{vectorizer_type.__name__}{VECTORIZER_FILE_EXT}"


def _load_model(model_type: Type[ModelType], vectorizer_type: Type[VectorizerType]) -> ModelType | None:
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


def _load_vocabulary(vectorizer_type: Type[VectorizerType]) -> dict[str, int]:
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


def get_vectorizer(vectorizer_type: Type[VectorizerType], vocabulary: dict[str, int]) -> VectorizerType:
    return vectorizer_type(ngram_range=N_GRAMS, strip_accents='unicode', decode_error='ignore', vocabulary=vocabulary)


def get_vocabulary_model(vectorizer_type: Type[VectorizerTypeType], model_type: Type[ModelType], train: bool = False) -> tuple[dict[str, int], ModelType]:
    """
    Load the vocabulary and model from file

    Args:
        vectorizer_type (type): _description_
        model_type (type): _description_
        train (bool, optional): _description_. Defaults to False.

    Raises:
        Exception: _description_
        Exception: _description_

    Returns:
        tuple[dict[str, int], ModelType]: _description_
    """
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
    """Save vocabulary and model to a file

    Args:
        vocabulary (dict[str, int]): vocabulary to save
        vectorizer_type (type): vectorizer type to not mix different formats
        model (ModelType): model to save
    """
    with open(_get_vectorizer_file_name(vectorizer_type=vectorizer_type), 'wb') as file_handle:
        pickle.dump(vocabulary, file_handle)
    with open(_get_model_file_name(model_type=type(model), vectorizer_type=vectorizer_type), 'wb') as file_handle:
        pickle.dump(model, file_handle)


def extend_vocabulary(documents: Iterable[str], vocabulary: dict[str, int], vectorizer: _VectorizerMixin):
    """Extend the vocabulary by documents' tokens

    Args:
        documents (Iterable[str]): documents to parse
        vocabulary (dict[str, int]): dictionary to extend
        vectorizer (_VectorizerMixin): vectorizer to analyse the documents with
    """
    analyze = vectorizer.build_analyzer()  # type:ignore
    for doc in documents:
        for feature in analyze(doc):  # type: ignore
            feature = str(feature).lower()  # type: ignore
            if feature not in vocabulary:
                vocabulary[feature] = len(vocabulary)  # type: ignore
