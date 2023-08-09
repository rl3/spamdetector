

import os
import pickle
import threading
from itertools import chain
from typing import Iterable

import sklearn.feature_extraction.text  # type:ignore
from nltk import download  # type:ignore
from nltk.corpus import stopwords  # type:ignore

from constants import (MODEL_FILE_EXT, MODEL_FILE_PREFIX, N_GRAMS,
                       TEXT_MODEL_TYPE, TEXT_VECTORIZER_TYPE,
                       VECTORIZER_FILE_EXT, VOCABULARY_FILE_PREFIX,
                       MailContent, TextModelType, TextVectorizerType)

STRIP_ACCENTS = sklearn.feature_extraction.text.strip_accents_unicode
download('stopwords')
STOPWORDS: list[str] = [
    STRIP_ACCENTS(word)
    for word in stopwords.words(['german', 'english'])  # type:ignore
]
# print(STOPWORDS)
# exit()


class SpamDetector:
    def __init__(self, train: bool = False) -> None:
        self.train: bool = train
        self._lock = threading.Lock()
        self.reload()

    def reload(self):
        with self._lock:
            self.vocabulary, self.model = self._get_vocabulary_model(
                self.train)
            self.vectorizer = TEXT_VECTORIZER_TYPE(
                ngram_range=N_GRAMS,
                strip_accents=STRIP_ACCENTS,
                decode_error='ignore',
                vocabulary=self.vocabulary,
                stop_words=STOPWORDS,
            )

    def _get_model_vectorizer(self) -> tuple[TextModelType, TextVectorizerType]:
        with self._lock:
            return (self.model, self.vectorizer)

    def _get_vocabulary_model(self, train: bool = False) -> tuple[dict[str, int], TextModelType]:
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
                return (vocabulary, TEXT_MODEL_TYPE())
            raise Exception(  # pylint: disable=broad-exception-raised
                "Could not load vectorizer")

        model = self._load_model()
        if model is None:
            if train:
                return (vocabulary, TEXT_MODEL_TYPE())
            raise Exception(  # pylint: disable=broad-exception-raised
                "Could not load model")

        return (vocabulary, model)

    def _get_model_file_name(self) -> str:
        return f"{MODEL_FILE_PREFIX}-{TEXT_MODEL_TYPE.__name__}-{TEXT_VECTORIZER_TYPE.__name__}-{N_GRAMS}{MODEL_FILE_EXT}"

    def _get_vocabulary_file_name(self) -> str:
        return f"{VOCABULARY_FILE_PREFIX}-{TEXT_VECTORIZER_TYPE.__name__}-{N_GRAMS}{VECTORIZER_FILE_EXT}"

    def _load_model(self) -> TextModelType | None:
        file_name = self._get_model_file_name()
        try:
            if os.path.isfile(file_name) and os.access(file_name, os.R_OK):
                with open(file_name, 'rb') as file_handle:
                    print(f"Loding model from file '{file_name}'")
                    model = pickle.load(file_handle)
                    if isinstance(model, TEXT_MODEL_TYPE):
                        return model
                    print(
                        f"Object in file '{file_name}' has wrong type. Expected '{TEXT_MODEL_TYPE.__name__}' got '{type(model).__name__}'")
        except:  # pylint: disable=bare-except
            print(f"Loding model from file '{file_name}' failed")
        return None

    def _load_vocabulary(self) -> dict[str, int]:
        file_name = self._get_vocabulary_file_name()
        try:
            if os.path.isfile(file_name) and os.access(file_name, os.R_OK):
                with open(file_name, 'rb') as file_handle:
                    print(f"Loading vocabulary from file '{file_name}'")
                    vocabulary = pickle.load(file_handle)
                    return vocabulary

        except:  # pylint: disable=bare-except
            print(f"Loading vocabulary from file '{file_name}' failed")
        return {}

    def save_vocabulary_model(self):
        """Save vocabulary and model to a file

        Args:
            vocabulary (dict[str, int]): vocabulary to save
            vectorizer_type (type): vectorizer type to not mix different formats
            model (ModelType): model to save
        """

        with self._lock:
            with open(self._get_vocabulary_file_name(), 'wb') as file_handle:
                pickle.dump(self.vocabulary, file_handle)
            with open(self._get_model_file_name(), 'wb') as file_handle:
                pickle.dump(self.model, file_handle)

    def get_features(  # type:ignore
            self, contents: list[MailContent], vectorizer: TextVectorizerType
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

        with self._lock:
            for doc in documents:
                for feature in analyze(doc):  # type: ignore
                    feature = str(feature).lower()  # type: ignore
                    if feature not in self.vocabulary:
                        self.vocabulary[feature] = len(
                            self.vocabulary)

    def predict_mail(self, content: MailContent) -> bool:
        model, vectorizer = self._get_model_vectorizer()
        features_predict = self.get_features(  # type:ignore
            contents=[content],
            vectorizer=vectorizer
        )

        # prediction_values = model.predict_proba(features_predict)
        predictions = model.predict(features_predict)  # type:ignore
        return bool(predictions[0] == 'spam')

    def learn_mail(self, contents: list[MailContent], labels: list[str]):
        with self._lock:
            self.extend_vocabulary(
                documents=chain.from_iterable(contents),
            )

            features = self.get_features(  # type:ignore
                contents=contents,
                vectorizer=self.vectorizer
            )

            self.model.fit(features, labels)  # type:ignore
