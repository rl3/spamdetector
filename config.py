import re
import socket

# TODO: Should be configurable

# Directory to scan if spam_learn.py is started without parameter
MAIL_DIRS = ["mails"]

# Regular expressions for pathes of mail files that should be treated as spam
RE_SPAM_PATH: list[tuple[str, re.RegexFlag] | str] = [
    (r'\bspam\b', re.IGNORECASE),
]

# Regular expressions for pathes of mail files that should be ignored
RE_TRASH_PATH: list[tuple[str, re.RegexFlag] | str] = [
    (r'\btrash\b', re.IGNORECASE),
    (r'\bdeleted\b', re.IGNORECASE),
]

# Regular expressions to be removed from mail's subject to not be biased
RE_SPAM_SUBJECT_PREFIX: list[tuple[str, re.RegexFlag] | str] = [
    (r'^\s*\*+\s*SPAM\s*\*+\s*', re.IGNORECASE),
    (r'^\s*\*+\s*AI\-SPAM\s*\*+\s*', re.IGNORECASE),
]

# Recipients to skip the spam filter for
RE_RECIPIENTS_TO_IGNORE: list[str] = []

# Recipients to apply the spam filter for
RE_RECIPIENTS_TO_APPLY: list[str] = [
    r'(?:test|huhu)\@steppicrew\.de',
]

# Prefix to prefix the subject of detected spam mails with
SUBJECT_PREFIX: str | None = "*** AI-SPAM ***"

# Languages to load stop words for
STOP_WORD_LANGUANGES: list[str] = ["german", "english"]

# The socket to create for the daemon
# Examples:
#   socket.AF_UNIX, './spam.sock'
#   socket.AF_INET, ('localhost', 10028)
SOCKET_DATA: tuple[int, str | tuple[str, int]] = (
    socket.AF_UNIX, './spam.sock'
)
