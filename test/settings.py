# Rabbitmq
RABBIT_HOST = '127.0.0.1'
RABBIT_PORT = 5672
RABBIT_USERNAME = 'yuntom'
RABBIT_PASSWORD = '123456'
RABBIT_VIRTUAL_HOST = '/'

# redis
REDIS_QUEUE_HOST = '127.0.0.1'
REDIS_QUEUE_PORT = 6379
REDIS_QUEUE_DB = 1

# 日志等级
LOG_LEVEL = 'ERROR'

# 中间件
MIDDLEWARES = ['middlewares.TestMiddleware']

# 管道
ITEM_PIPELINES = ['pipelines.TestPipeline']

# 最大重试次数
MAX_RETRY = 5
