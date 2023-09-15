import re
import socket

from constants import LOG_INFO, LogPriorityType

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

# Only run mail_filter if the last matching expression on the reciving address is True
RE_RECIPIENTS_FILTER: list[tuple[str, bool]] = [
    (r'.+', False),  # do not run for any address
    (r'(?:test|huhu)\@steppicrew\.de', True),  # run for those addresses
]

# Prefix to prefix the subject of detected spam mails with
SUBJECT_PREFIX: str | None = "*** AI-SPAM ***"

# Languages to load stop words for
STOP_WORD_LANGUANGES: list[str] = ["german", "english"]

# The socket to create for the daemon
# Examples:
#   socket.AF_UNIX, './spam.sock'
#   socket.AF_INET, ('localhost', 10028)
RECEIVING_SOCKET_DATA: tuple[int, str | tuple[str, int]] = (
    # socket.AF_UNIX, './spam.sock'
    socket.AF_INET, ('localhost', 10025)
)
SENDING_SOCKET_DATA: str = './sink.sock'
# SENDING_SOCKET_DATA: str = 'localhost:10026'

LOG_FILE: str = './mail_filter.log'
LOG_LEVEL: LogPriorityType = LOG_INFO
