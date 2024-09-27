import os
import sys
from loguru import logger


class Logger(object):
    def __init__(self, settings, name):
        log_path = settings.get('LOG_FILE')
        if log_path:
            if log_path.startswith('.'):
                log_path = os.path.join(settings.get('BOT_DIR'), log_path)
            logger.add("%s/rabbit_{time:YYYY-MM-DD}.log" % log_path,
                       level=settings.get('LOG_LEVEL', 'ERROR'),
                       rotation="1 day",
                       retention="1 week",
                       format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {extra[scope]} | {message}")
        else:
            logger.add(sink=sys.stderr,
                       level=settings.get('LOG_LEVEL', 'ERROR'),
                       format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {extra[scope]} | {message}")
        self.logger = logger.bind(scope=name)

    def info(self, msg):
        self.logger.info(msg)

    def warning(self, msg):
        self.logger.warning(msg)

    def error(self, msg):
        self.logger.error(msg)
