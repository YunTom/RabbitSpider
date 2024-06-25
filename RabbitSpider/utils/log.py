from loguru import logger


class Logger(object):
    def __init__(self, settings, name):
        logger.add("%s/rabbit_{time:YYYY-MM-DD}.log" % settings.get('LOG_FILE'), level=settings.get('LOG_LEVEL'),
                   rotation="1 day",
                   retention="1 week",
                   format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {extra[scope]} | {name}:{line} - {message}")
        self.logger = logger.bind(scope=name)

    def log(self, msg):
        self.logger.info(msg)

    def warning(self, msg):
        self.logger.warning(msg)

    def error(self, msg):
        self.logger.error(msg)
