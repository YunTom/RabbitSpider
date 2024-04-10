# DOWNLOAD
from RabbitSpider.core.download import AiohttpDownload, CurlDownload

# Rabbitmq
RABBIT_HOST = '121.36.225.245'
RABBIT_PORT = 5672
RABBIT_USERNAME = 'yuntom'
RABBIT_PASSWORD = '123456'
RABBIT_VIRTUAL_HOST = '/'

# redis
REDIS_FILTER_NAME = 'filter_queue'
REDIS_QUEUE_HOST = '127.0.0.1'
REDIS_QUEUE_PORT = 6379
REDIS_QUEUE_DB = 1

# 下载器
DOWNLOAD = CurlDownload


