from typing import Literal

SPAM_DIR = "spam"
HAM_DIR = "ham"

MODEL_FILE_PREFIX = "model"
MODEL_FILE_EXT = ".pkl"

NEW_MODEL: bool = False

VOCABULARY_FILE_PREFIX = "vocabulary"
VOCABULARY_FILE_EXT = ".pkl"

TEXT_TRANSFORMER: Literal['CountVectorizer',
                          'TfidfTransformer', 'TfidfVectorizer'] = 'CountVectorizer'
TEXT_MODEL: Literal['SVC', 'MultinomialNB'] = 'SVC'

MAX_SIZE = 50_000
TRAIN_CHUNK_SIZE = 1_000

LIMIT_FILES: int | None = None  # 1000
