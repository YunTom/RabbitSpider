import os, sys
from loguru import logger


class Logger(object):
    def __init__(self, settings, name):
        log_path = settings.get('LOG_FILE')
        if log_path:
            for root, dirs, files in os.walk(os.path.abspath(os.path.join(sys.argv[0],'../..'))):
                if log_path.split('/')[0] == os.path.basename(root):
                    log_dir = os.path.join(root, log_path.split('/')[1])
                    logger.add("%s/rabbit_{time:YYYY-MM-DD}.log" % log_dir,
                               level=settings.get('LOG_LEVEL', 'ERROR'),
                               rotation="1 day",
                               retention="1 week",
                               format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {extra[scope]} | {name}:{line} - {message}")
                    self.logger = logger.bind(scope=name)
                    break
        else:
            self.logger = logger

    def info(self, msg):
        self.logger.info(msg)

    def warning(self, msg):
        self.logger.warning(msg)

    def error(self, msg):
        self.logger.error(msg)
