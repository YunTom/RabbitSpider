import os
import sys
from loguru import logger


class Logger(object):
    def __init__(self, settings, name):
        logger.remove()
        log_path = os.path.join(settings.get('BOT_DIR'), settings.get('LOG_FILE')) if settings.get(
            'LOG_FILE') and settings.get('LOG_FILE').startswith('.') else settings.get('LOG_FILE')
        if log_path:
            logger.add("%s/rabbit_{time:YYYY-MM-DD}.log" % log_path,
                       level=settings.get('LOG_LEVEL', 'ERROR'),
                       rotation="1 day",
                       retention="1 week",
                       format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{extra[scope]}</cyan> | <level>{message}</level>")

        logger.add(sink=sys.stdout,
                   colorize=True,
                   level='INFO',
                   format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{extra[scope]}</cyan> | <level>{message}</level>")
        self._logger = logger.bind(scope=name)

    def info(self, msg):
        self._logger.info(msg)

    def warning(self, msg):
        self._logger.warning(msg)

    def error(self, msg):
        self._logger.error(msg)
