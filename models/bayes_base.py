import os
import pickle
from itertools import chain
from sqlite3 import OperationalError
from typing import Callable, Generic, Iterable, TypeVar

import sklearn.feature_extraction.text  # type:ignore
from nltk import download  # type:ignore
from nltk.corpus import stopwords  # type:ignore
from sklearn.feature_extraction.text import CountVectorizer  # type: ignore
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB  # type: ignore
from sklearn.svm import SVC  # type: ignore

from config import DATA_DIR, STOP_WORD_LANGUANGES
from constants import (MODEL_FILE_EXT, MODEL_FILE_PREFIX, N_GRAMS,
                       VECTORIZER_FILE_EXT, VOCABULARY_FILE_PREFIX)
from mail_logging import LOG_DEBUG, LOG_ERROR, LOG_INFO, LOG_WARN
from mail_logging.logging import log
from mail_types import MailContent
from models.base import SpamDetectorModelBase

VectorizerType = TypeVar('VectorizerType', CountVectorizer, TfidfVectorizer)
ModelType = TypeVar('ModelType', SVC, MultinomialNB)

STRIP_ACCENTS = sklearn.feature_extraction.text.strip_accents_unicode


def ___closure1() -> Callable[[], list[str]]:

    _stop_words: list[str] | None = None

    def _get_stop_words():
        nonlocal _stop_words
        if _stop_words is not None:
            return _stop_words

        download('stopwords')
        _stop_words = [
            STRIP_ACCENTS(word)
            for word in stopwords.words(STOP_WORD_LANGUANGES)  # type:ignore
        ]
        return _stop_words

    return _get_stop_words


get_stop_words = ___closure1()


class SpamDetectorModelBayesBase(SpamDetectorModelBase, Generic[VectorizerType, ModelType]):
    def __init__(self, vectorizer_class: type[VectorizerType], model_class: type[ModelType], for_training: bool = False) -> None:
        super().__init__()
        self.vectorizer_class: type[VectorizerType] = vectorizer_class
        self.model_class: type[ModelType] = model_class
        self.vocabulary: dict[str, int]
        self.vectorizer: VectorizerType
        self.model: ModelType
        self.initialized: bool = False

    def load_model(self):
        with self.lock:
            self.vocabulary, self.model = self._get_vocabulary_model(
                self.for_training)
            self.vectorizer = self.vectorizer_class(
                ngram_range=N_GRAMS,
                strip_accents=STRIP_ACCENTS,
                decode_error='ignore',
                vocabulary=self.vocabulary,
                stop_words=get_stop_words(),
            )
            self.initialized = True

    def _get_model_vectorizer(self) -> tuple[ModelType, VectorizerType]:
        with self.lock:
            if not self.initialized:
                self.load_model()
            return (self.model, self.vectorizer)

    def _get_vocabulary_model(self, train: bool = False) -> tuple[dict[str, int], ModelType]:
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
        vocabulary = self._load_vocabulary()
        if len(vocabulary) == 0:
            if train:
                # type: ignore
                return (vocabulary, self.model_class())
            raise OperationalError("Could not load vectorizer")

        model = self._load_model()
        if model is None:
            if train:
                return (vocabulary, self.model_class())
            raise OperationalError("Could not load model")

        return (vocabulary, model)

    def _get_model_file_name(self) -> str:
        return os.path.join(
            os.path.abspath(DATA_DIR),
            f"{MODEL_FILE_PREFIX}-{self.model_class.__name__}-{self.vectorizer_class.__name__}-{N_GRAMS}{MODEL_FILE_EXT}"
        )

    def _get_vocabulary_file_name(self) -> str:
        return os.path.join(
            os.path.abspath(DATA_DIR),
            f"{VOCABULARY_FILE_PREFIX}-{self.vectorizer_class.__name__}-{N_GRAMS}{VECTORIZER_FILE_EXT}"
        )

    def _load_model(self) -> ModelType | None:
        file_name = self._get_model_file_name()
        try:
            if os.path.isfile(file_name) and os.access(file_name, os.R_OK):
                with open(file_name, 'rb') as file_handle:
                    log(LOG_INFO, f"Loding model from file '{file_name}'")
                    model = pickle.load(file_handle)
                    log(LOG_DEBUG,
                        f"Loding model from file '{file_name}' done")
                    if isinstance(model, self.model_class):
                        return model
                    log(
                        LOG_ERROR,
                        f"Object in file '{file_name}' has wrong type. Expected '{self.model_class.__name__}' got '{type(model).__name__}'"
                    )
        except:  # pylint: disable=bare-except
            log(LOG_WARN, f"Loding model from file '{file_name}' failed")
        return None

    def _load_vocabulary(self) -> dict[str, int]:
        file_name = self._get_vocabulary_file_name()
        try:
            if os.path.isfile(file_name) and os.access(file_name, os.R_OK):
                with open(file_name, 'rb') as file_handle:
                    log(LOG_INFO,
                        f"Loading vocabulary from file '{file_name}'")
                    vocabulary = pickle.load(file_handle)
                    log(LOG_DEBUG,
                        f"Loading vocabulary from file '{file_name}' done")
                    return vocabulary

        except:  # pylint: disable=bare-except
            log(LOG_WARN, f"Loading vocabulary from file '{file_name}' failed")
        return {}

    def save_model(self):
        """Save vocabulary and model to a file

        Args:
            vocabulary (dict[str, int]): vocabulary to save
            vectorizer_type (type): vectorizer type to not mix different formats
            model (ModelType): model to save
        """

        with self.lock:
            with open(self._get_vocabulary_file_name(), 'wb') as file_handle:
                pickle.dump(self.vocabulary, file_handle)
            with open(self._get_model_file_name(), 'wb') as file_handle:
                pickle.dump(self.model, file_handle)

    def get_features(  # type:ignore
            self, contents: list[MailContent], vectorizer: VectorizerType
    ):
        if len(contents) == 0:
            return None

        features = None
        for i in range(len(contents[0])):
            _features = vectorizer.fit_transform(  # type:ignore
                [c[i] for c in contents]
            )
            if features is None:
                features = _features  # type:ignore
            else:
                features += _features  # type:ignore
        return features  # type:ignore

    def extend_vocabulary(self, documents: Iterable[str]):
        """Extend the vocabulary by documents' tokens

        Args:
            documents (Iterable[str]): documents to parse
        """

        analyze = self.vectorizer.build_analyzer()  # type:ignore

        with self.lock:
            for doc in documents:
                for feature in analyze(doc):  # type: ignore
                    feature = str(feature).lower()  # type: ignore
                    if feature not in self.vocabulary:
                        self.vocabulary[feature] = len(
                            self.vocabulary)

    def predict_mail(self, content: MailContent) -> bool:
        model, vectorizer = self._get_model_vectorizer()
        log(LOG_DEBUG, "Getting features.")
        features_predict = self.get_features(  # type:ignore
            contents=[content],
            vectorizer=vectorizer
        )

        log(LOG_DEBUG, "Predicting...")

        # prediction_values = model.predict_proba(features_predict)
        predictions = model.predict(features_predict)  # type:ignore

        log(LOG_DEBUG, f"Prediction finished: {predictions[0]}")
        return bool(predictions[0] == 'spam')

    def learn_mails(self, contents: list[MailContent], labels: list[str]):
        with self.lock:
            self.extend_vocabulary(
                documents=chain.from_iterable(contents),
            )

            features = self.get_features(  # type:ignore
                contents=contents,
                vectorizer=self.vectorizer
            )

            self.model.fit(features, labels)  # type:ignore
