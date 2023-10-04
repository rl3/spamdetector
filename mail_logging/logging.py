import logging
import os
import syslog
from typing import Any

from mail_logging import (LOG_DEBUG, LOG_ERROR, LOG_FILE_CONSOLE,
                          LOG_FILE_SYSLOG, LOG_INFO, LOG_WARN, LogPriorityType)


class _LogBase:
    def log(self, priority: LogPriorityType, message: str) -> None:
        raise NotImplementedError


class _LogSyslog(_LogBase):
    def __init__(self) -> None:
        super().__init__()
        self.level_mapper: dict[LogPriorityType, int] = {
            LOG_DEBUG: syslog.LOG_DEBUG,
            LOG_INFO: syslog.LOG_INFO,
            LOG_WARN: syslog.LOG_WARNING,
            LOG_ERROR: syslog.LOG_ERR,
        }

    def log(self, priority: LogPriorityType, message: str) -> None:
        syslog.syslog(
            self.level_mapper.get(priority, priority),
            message
        )


class _LogFile(_LogBase):
    def __init__(self, file_name: str, log_level: LogPriorityType) -> None:
        super().__init__()
        self.level_mapper: dict[LogPriorityType, int] = {
            LOG_DEBUG: logging.DEBUG,
            LOG_INFO: logging.INFO,
            LOG_WARN: logging.WARNING,
            LOG_ERROR: logging.ERROR,
        }
        level = self.level_mapper.get(log_level, logging.INFO)
        logging.basicConfig(
            filename=file_name,
            level=level,
            format='%(asctime)s %(levelname)s %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
        )

    def log(self, priority: LogPriorityType, message: str) -> None:
        logging.log(
            level=self.level_mapper.get(priority, logging.INFO),
            msg=message
        )


class _LogConsole(_LogBase):
    def __init__(self, log_level: LogPriorityType) -> None:
        super().__init__()
        self.log_level = log_level

    def log(self, priority: LogPriorityType, message: str) -> None:
        if priority >= self.log_level:
            print(message)


_logger: _LogBase = _LogConsole(LOG_INFO)


def log(priority: LogPriorityType, *messages: Any):
    _logger.log(
        priority=priority,
        message=(
            f"[{os.getpid()}] " +
            ' '.join(str(message) for message in messages)
        )
    )


def init_logger(log_file: str, log_level: LogPriorityType = LOG_INFO) -> None:
    global _logger
    _logger = (
        _LogSyslog()
        if log_file == LOG_FILE_SYSLOG
        else _LogConsole(log_level)
        if log_file == LOG_FILE_CONSOLE
        else _LogFile(log_file, log_level)
    )
