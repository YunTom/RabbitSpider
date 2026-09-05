import sys
from pathlib import Path
from typing import Any
from loguru import logger


class LogManager:
    DEFAULT_COMPONENT = "RabbitSpider"

    LOG_FORMAT = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{extra[component]}</cyan> | "
        "<level>{message}</level>"
    )

    def __init__(self, settings: dict[str, Any]) -> None:
        self.settings = settings

        logger.remove()

        self._configure_file()
        self._configure_console()

        self._logger = logger

    def _configure_file(self) -> None:
        log_file = self.settings.get("LOG_FILE")

        if not log_file:
            return

        bot_dir = self.settings.get("BOT_DIR", "")
        log_path = self._resolve_log_path(log_file, bot_dir)

        log_path.mkdir(parents=True, exist_ok=True)

        logger.add(
            log_path / "rabbit_{time:YYYY-MM-DD}.log",
            level=self.settings.get("LOG_LEVEL", "ERROR"),
            rotation="1 day",
            retention="1 week",
            compression="zip",
            encoding="utf-8",
            format=self.LOG_FORMAT,
            enqueue=True,
            backtrace=True,
            diagnose=False,
        )

    @staticmethod
    def _resolve_log_path(log_file: str, bot_dir: str) -> Path:
        path = Path(log_file)

        if path.is_absolute():
            return path

        if log_file.startswith("."):
            return Path(bot_dir) / path

        return path

    def _configure_console(self) -> None:
        logger.add(
            sys.stdout,
            level="INFO",
            colorize=True,
            format=self.LOG_FORMAT,
            enqueue=True,
        )

    def _get_scoped_logger(self, component: str):
        return self._logger.bind(component=component)

    def debug(self, msg: str, component: str = DEFAULT_COMPONENT) -> None:
        self._get_scoped_logger(component).debug(msg)

    def info(self, msg: str, component: str = DEFAULT_COMPONENT) -> None:
        self._get_scoped_logger(component).info(msg)

    def warning(self, msg: str, component: str = DEFAULT_COMPONENT) -> None:
        self._get_scoped_logger(component).warning(msg)

    def error(self, msg: str, component: str = DEFAULT_COMPONENT) -> None:
        self._get_scoped_logger(component).error(msg)

    def critical(self, msg: str, component: str = DEFAULT_COMPONENT) -> None:
        self._get_scoped_logger(component).critical(msg)

    def exception(self, msg: str, component: str = DEFAULT_COMPONENT) -> None:
        self._get_scoped_logger(component).exception(msg)

    def bind(self, component: str):
        return self._get_scoped_logger(component)
