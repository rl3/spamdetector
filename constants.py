from typing import Tuple, Type, Union

from sklearn.feature_extraction.text import CountVectorizer  # type: ignore
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB  # type: ignore
from sklearn.svm import SVC  # type: ignore

MODEL_FILE_PREFIX = "model"
MODEL_FILE_EXT = ".pkl"

NEW_MODEL: bool = False

VOCABULARY_FILE_PREFIX = "vocabulary"
VECTORIZER_FILE_EXT = ".pkl"

TextVectorizerType = Union[
    CountVectorizer,
    TfidfVectorizer,
]
TEXT_VECTORIZER_TYPE: Type[TextVectorizerType] = TfidfVectorizer
N_GRAMS: tuple[int, int] = (1, 2)
TextModelType = Union[
    SVC,
    MultinomialNB,
]
TEXT_MODEL_TYPE: Type[TextModelType] = MultinomialNB

MAX_SIZE = 50_000
TRAIN_CHUNK_SIZE = 1_000

MailContent = Tuple[str, ...]

SERVER_PORT_DEFAULT: int = 10025

SMTP_ERROR_CODE_554 = 554
