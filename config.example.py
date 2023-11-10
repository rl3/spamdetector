import re

from mail_logging import LOG_FILE_SYSLOG, LOG_INFO, LogPriorityType

# Directory to scan if spam_learn.py is started without parameter
DEFAULT_SPAM_LEARN_DIRS = ["mails"]

# Regular expressions for pathes of mail files that should be treated as spam
# Path is relative to scanned root path
RE_SPAM_PATH: list[tuple[str, re.RegexFlag] | str] = [
    (r'\bspam\b', re.IGNORECASE),
]

# Regular expressions for pathes of mail files that should be ignored
# Path is relative to scanned root path
RE_IGNORE_PATH: list[tuple[str, re.RegexFlag] | str] = [
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
    (r'(?:test|huhu)\@example\.com', True),  # run for those addresses
]

# Prefix to prefix the subject of detected spam mails with
SUBJECT_PREFIX: str | None = "*** AI-SPAM ***"

# Prefix for added mail header fields
MAIL_HEADER_FIELD_PREFIX = b"RL3-AI-Spam-Filter"

# Languages to load stop words for
STOP_WORD_LANGUANGES: list[str] = ["german", "english"]


# Directory to store vocabularies and models in
DATA_DIR: str = '/usr/local/lib/spamdetector/data'

# The socket to create for the daemon
# LISTENING_SOCKET_DATA: str = 'localhost:10025'
LISTENING_SOCKET_DATA: str = '/run/ai-spamdetector/ai-spamdetector.sock'
NEXT_PEER_SOCKET_DATA: str = './sink.sock'
# NEXT_PEER_SOCKET_DATA: str = 'localhost:10026'
DEFAULT_NEXT_PEER_PORT: int = 10026

# LOG_FILE: str = './mail_filter.log'
# LOG_FILE: str = LOG_FILE_CONSOLE
LOG_FILE: str = LOG_FILE_SYSLOG
LOG_LEVEL: LogPriorityType = LOG_INFO

LAST_LEARN_SEMAPHORE = f"{DATA_DIR}/last_learn.sem"
