from sklearn.feature_extraction.text import CountVectorizer  # type: ignore
from sklearn.naive_bayes import MultinomialNB  # type: ignore

from models.model_bayes_base import SpamDetectorModelBayesBase


class SpamDetectorModelCountMultinominal(SpamDetectorModelBayesBase[CountVectorizer, MultinomialNB]):
    def __init__(self, for_training: bool = False) -> None:
        super().__init__(
            vectorizer_class=CountVectorizer,
            model_class=MultinomialNB,
            for_training=for_training
        )
