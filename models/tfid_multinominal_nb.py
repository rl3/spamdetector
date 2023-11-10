from sklearn.feature_extraction.text import TfidfVectorizer  # type: ignore
from sklearn.naive_bayes import MultinomialNB  # type: ignore

from models.bayes_base import SpamDetectorModelBayesBase


class SpamDetectorModelTfidMultinominal(SpamDetectorModelBayesBase[TfidfVectorizer, MultinomialNB]):
    def __init__(self, for_training: bool = False) -> None:
        super().__init__(
            vectorizer_class=TfidfVectorizer,
            model_class=MultinomialNB,
            for_training=for_training
        )
