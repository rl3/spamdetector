from typing import Literal, Union

LOG_FILE_SYSLOG = 'syslog'
LOG_FILE_CONSOLE = 'console'

LogPriorityType = Union[Literal[0], Literal[1], Literal[2], Literal[3]]

LOG_DEBUG: LogPriorityType = 0
LOG_INFO: LogPriorityType = 1
LOG_WARN: LogPriorityType = 2
LOG_ERROR: LogPriorityType = 3
