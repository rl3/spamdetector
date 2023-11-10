"""
Daemon handling SpamDetector instance and reload on SIGHUB
"""

import signal
import threading
from email.message import EmailMessage
from types import FrameType

from config_model import SpamDetectorModel
from mail_logging import LOG_INFO
from mail_logging.logging import log
from models.model_base import SpamDetectorModelBase
from tools import read_mail


class AIFilterDaemon:
    """
    Threadsafe class providing SpamDetector instance and reloading on SIGHUB
    """

    def __init__(self) -> None:
        self._spam_detector_model: SpamDetectorModelBase | None = None
        self._lock = threading.RLock()
        self._original_hup_handler = signal.getsignal(signal.SIGHUP)

        def handle_sighup(_signum: int, _frame: FrameType | None):
            if self._spam_detector_model is None:
                log(LOG_INFO, "Not yet initialized. Do nothing.")
                return

            log(LOG_INFO, "Reloading model...")
            with self._lock:
                self._spam_detector_model.reload()
            log(LOG_INFO, "Done reloading model.")

        signal.signal(signal.SIGHUP, handler=handle_sighup)

    def __del__(self):
        signal.signal(signal.SIGHUP, handler=self._original_hup_handler)

    def _get_spam_detector(self):
        with self._lock:
            if self._spam_detector_model is not None:
                return self._spam_detector_model

            self._spam_detector_model = SpamDetectorModel()
            return self._spam_detector_model

    def predict_mail(self, mail_body: EmailMessage) -> tuple[bool, str]:
        prediction = self._get_spam_detector().predict_mail(
            content=read_mail(message=mail_body)
        )

        result = "SPAM" if prediction else "HAM"

        log(LOG_INFO, f"Parsing finished with classification {result}")

        return (prediction, result)
