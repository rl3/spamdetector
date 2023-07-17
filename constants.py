from typing import TypeVar, Type
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer  # type: ignore
from sklearn.naive_bayes import MultinomialNB  # type: ignore
from sklearn.svm import SVC  # type: ignore

SPAM_DIR = "spam"
HAM_DIR = "ham"

MODEL_FILE_PREFIX = "model"
MODEL_FILE_EXT = ".pkl"

NEW_MODEL: bool = False

VECTORIZER_FILE_PREFIX = "vocabulary"
VECTORIZER_FILE_EXT = ".pkl"

TextVectorizerTypes = TypeVar(
    "TextVectorizerTypes", CountVectorizer, TfidfVectorizer)
TEXT_VECTORIZER = TfidfVectorizer
ModelTypes = TypeVar("ModelTypes", SVC, MultinomialNB)
TEXT_MODEL = SVC

MAX_SIZE = 50_000
TRAIN_CHUNK_SIZE = 1_000

LIMIT_FILES: int | None = None  # 1000
