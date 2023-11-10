from typing import Type

from spam_detector_model_base import SpamDetectorModelBase
from spam_detector_model_TfidMultinominalNB import \
    SpamDetectorModelTfidMultinominal

SpamDetectorModel: Type[SpamDetectorModelBase] = SpamDetectorModelTfidMultinominal
