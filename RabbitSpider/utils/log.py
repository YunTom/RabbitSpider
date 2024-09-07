import os
from loguru import logger


class Logger(object):
    def __init__(self, spider):
        log_path = spider.settings.get('LOG_FILE')
        if log_path:
            if log_path.startswith('.'):
                log_path = os.path.abspath(os.path.join(os.path.abspath(spider.name), '../..', log_path))
            logger.add("%s/rabbit_{time:YYYY-MM-DD}.log" % log_path,
                       level=spider.settings.get('LOG_LEVEL', 'ERROR'),
                       rotation="1 day",
                       retention="1 week",
                       format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {extra[scope]} | {name}:{line} - {message}")
            self.logger = logger.bind(scope=spider.queue_name)
        else:
            self.logger = logger

    def info(self, msg):
        self.logger.info(msg)

    def warning(self, msg):
        self.logger.warning(msg)

    def error(self, msg):
        self.logger.error(msg)
