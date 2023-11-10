from typing import Type

from models.base import SpamDetectorModelBase
from models.tfid_multinominal_nb import SpamDetectorModelTfidMultinominal

SpamDetectorModel: Type[SpamDetectorModelBase] = SpamDetectorModelTfidMultinominal
