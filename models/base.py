import threading
from mail_types import MailContent


class SpamDetectorModelBase():
    def __init__(self, for_training: bool = False) -> None:
        self.lock = threading.RLock()
        self.for_training = for_training

    def reload(self) -> None:
        self.load_model()

    def load_model(self) -> None:
        raise NotImplementedError()

    def save_model(self) -> None:
        raise NotImplementedError()

    def learn_mails(self, contents: list[MailContent], labels: list[str]) -> None:
        raise NotImplementedError()

    def predict_mail(self, content: MailContent) -> bool:
        raise NotImplementedError()
