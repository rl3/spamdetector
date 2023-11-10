from typing import Type

from models.base import SpamDetectorModelBase
from models.model_TfidMultinominalNB import SpamDetectorModelTfidMultinominal

SpamDetectorModel: Type[SpamDetectorModelBase] = SpamDetectorModelTfidMultinominal
