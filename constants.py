MODEL_FILE_PREFIX = "model"
MODEL_FILE_EXT = ".pkl"

NEW_MODEL: bool = False

VOCABULARY_FILE_PREFIX = "vocabulary"
VECTORIZER_FILE_EXT = ".pkl"

N_GRAMS: tuple[int, int] = (1, 2)

# TextVectorizerType = Union[
#    CountVectorizer,
#    TfidfVectorizer,
# ]
# TEXT_VECTORIZER_TYPE: Type[TextVectorizerType] = TfidfVectorizer
# TextModelType = Union[
#    SVC,
#    MultinomialNB,
# ]
# TEXT_MODEL_TYPE: Type[TextModelType] = MultinomialNB

MAX_SIZE = 50_000
TRAIN_CHUNK_SIZE = 1_000

SERVER_PORT_DEFAULT: int = 10025
NEXT_PEER_PORT_DEFAULT: int = 10026

SMTP_ERROR_CODE_554 = 554
