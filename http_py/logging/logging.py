import os
import sys
import logging
import warnings
from enum import Enum
from typing import Any, Final, NamedTuple
from collections.abc import Callable


class LogLevel(Enum):
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


LOG_LEVELS: Final[list[LogLevel]] = [
    LogLevel.DEBUG,
    LogLevel.INFO,
    LogLevel.WARNING,
    LogLevel.ERROR,
    LogLevel.CRITICAL,
]


class OsLoggingConfig(NamedTuple):
    environment_name: str
    log_level_console: LogLevel = LogLevel.DEBUG


def _load_log_level() -> LogLevel:
    log_level_console_: str | None = os.environ.get("LOG_LEVEL")
    if not log_level_console_:
        msg = (
            "OS ENV variable `LOG_LEVEL` is not set. Fallback to default "
            f"console log level: {LogLevel.DEBUG}."
        )
        warnings.warn(msg, stacklevel=2)
        return LogLevel.DEBUG
    try:
        return LogLevel[log_level_console_.upper()]
    except KeyError:
        msg = (
            f"Invalid OS ENV `LOG_LEVEL` '{log_level_console_}'. Value may "
            "be single level of: "
            f"{', '.join([level.name.upper() for level in LogLevel])}. Fallback to "
            f"default console log level {LogLevel.DEBUG}."
        )
        warnings.warn(msg, stacklevel=2)
        return LogLevel.DEBUG


def log_to_dict(
    logger_function: Callable[[dict[str, object]], None],
    msg: object,
    *args: Any,
    **kwargs: Any,
) -> None:
    log_as_dict: dict[str, object] = {
        "level": f"{logger_function.__name__}:",
        "message": msg,
    }
    args_as_dict: dict[str, object] = {
        str(pos): str(value) for pos, value in enumerate(args)
    }
    return logger_function(
        {**log_as_dict, **args_as_dict},
        **kwargs,
    )


class CustomLogger(logging.Logger):
    def __init__(self, name: str) -> None:
        super().__init__(name)
        log_level = _load_log_level()

        self.setLevel(log_level.value)

        # Console Handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level.value)
        console_format = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        console_handler.setFormatter(console_format)
        self.addHandler(console_handler)

    def debug(self, msg: object, *args: object, **kwargs: object) -> None:
        return log_to_dict(super().debug, msg, *args, **kwargs)

    def info(self, msg: object, *args: object, **kwargs: object) -> None:
        return log_to_dict(super().info, msg, *args, **kwargs)

    def warning(self, msg: object, *args: object, **kwargs: object) -> None:
        return log_to_dict(super().warning, msg, *args, **kwargs)

    def error(self, msg: object, *args: object, **kwargs: object) -> None:
        return log_to_dict(super().error, msg, *args, **kwargs)

    def critical(self, msg: object, *args: object, **kwargs: object) -> None:
        return log_to_dict(super().critical, msg, *args, **kwargs)


loggers: dict[str, CustomLogger] = {}


def create_logger(name: str = "root") -> CustomLogger:
    if name in loggers:
        return loggers[name]

    logger = CustomLogger(name)
    loggers[name] = logger
    return logger
