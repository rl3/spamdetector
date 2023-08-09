import re
import socket
from typing import Tuple, Type, Union

from sklearn.feature_extraction.text import CountVectorizer  # type: ignore
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB  # type: ignore
from sklearn.svm import SVC  # type: ignore

MAIL_DIR = "mails"
RE_SPAM_PATH: list[tuple[str, re.RegexFlag] | str] = [
    (r'\bspam\b', re.IGNORECASE),
]

MODEL_FILE_PREFIX = "model"
MODEL_FILE_EXT = ".pkl"

NEW_MODEL: bool = False

VOCABULARY_FILE_PREFIX = "vocabulary"
VECTORIZER_FILE_EXT = ".pkl"

TextVectorizerType = Union[
    CountVectorizer,
    TfidfVectorizer,
]
TEXT_VECTORIZER_TYPE: Type[TextVectorizerType] = CountVectorizer
N_GRAMS: tuple[int, int] = (1, 2)
TextModelType = Union[
    SVC,
    MultinomialNB,
]
TEXT_MODEL_TYPE: Type[TextModelType] = MultinomialNB

MAX_SIZE = 50_000
TRAIN_CHUNK_SIZE = 1_000

SOCKET_TYPE = 'INET'

SOCKET_INET: tuple[int, str | tuple[str, int]] = (
    socket.AF_INET, ('localhost', 10028)
)
SOCKET_UNIX: tuple[int, str | tuple[str, int]] = (
    socket.AF_UNIX, './spam.sock'
)
SOCKET_DATA = SOCKET_UNIX
MailContent = Tuple[str, ...]
