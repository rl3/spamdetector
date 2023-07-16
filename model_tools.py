
from constants import MODEL_FILE_PREFIX, MODEL_FILE_EXT, VOCABULARY_FILE_PREFIX, VOCABULARY_FILE_EXT, TEXT_TRANSFORMER, TEXT_MODEL, NEW_MODEL
import os
import pickle
from typing import Union
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer, TfidfTransformer  # type: ignore
from sklearn.naive_bayes import MultinomialNB  # type: ignore
from sklearn.svm import SVC  # type: ignore

ModelType = Union[SVC, MultinomialNB]
TransformerType = Union[CountVectorizer, TfidfTransformer, TfidfVectorizer]


def _get_model_file_name() -> str:
    return f"{MODEL_FILE_PREFIX}-{TEXT_MODEL}-{TEXT_TRANSFORMER}{MODEL_FILE_EXT}"


def _get_vocabulary_file_name() -> str:
    return f"{VOCABULARY_FILE_PREFIX}-{TEXT_TRANSFORMER}{VOCABULARY_FILE_EXT}"


def get_model(train: bool = False) -> ModelType:
    if not NEW_MODEL or not train:
        file_name = _get_model_file_name()
        try:
            if os.path.isfile(file_name) and os.access(file_name, os.R_OK):
                with open(file_name, 'rb') as file_handle:
                    print(f"Loding model from file '{file_name}'")
                    return pickle.load(file_handle)
        except:
            print(f"Loding model from file '{file_name}' failed")

    if TEXT_MODEL == 'MultinomialNB':
        return MultinomialNB(probability=True)

    return SVC(probability=True)


def _get_vocabulary() -> dict[str, int] | None:
    try:
        file_name = _get_vocabulary_file_name()
        if os.path.isfile(file_name) and os.access(file_name, os.R_OK):
            with open(file_name, 'rb') as file_handle:
                print(f"Loading vocabulary from file '{file_name}'")
                return pickle.load(file_handle)
    except:
        print(f"Loading vocabulary from file '{file_name}' failed")

    return None


def get_transformer() -> TransformerType:
    vocabulary = _get_vocabulary()
    if TEXT_TRANSFORMER == 'TfidfTransformer':
        return TfidfTransformer(vocabulary=vocabulary)
    if TEXT_TRANSFORMER == 'TfidfVectorizer':
        return TfidfVectorizer(vocabulary=vocabulary)
    return CountVectorizer(vocabulary=vocabulary)


def save_model(model: ModelType):
    file_name = _get_model_file_name()
    with open(file_name, 'wb') as file_handle:
        pickle.dump(model, file_handle)


def save_transformer(transformer: TransformerType):
    file_name = _get_vocabulary_file_name()

    with open(file_name, 'wb') as file_handle:
        pickle.dump(transformer.vocabulary_, file_handle)
