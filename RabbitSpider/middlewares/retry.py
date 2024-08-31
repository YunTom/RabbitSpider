from RabbitSpider.middlewares import BaseMiddleware


class RetryMiddleware(BaseMiddleware):
    def __init__(self, spider):
        super().__init__(spider)
        self.retry_http_code = spider.settings.getlist('RETRY_HTTP_CODES')
        self.retry_exceptions = spider.settings.getlist('RETRY_EXCEPTIONS')
        self.max_retry = spider.settings.get('MAX_RETRY')

    async def process_response(self, request, response, spider):
        if response.status in self.retry_http_code:
            if request.retry < self.max_retry:
                request.retry += 1
                return request
            else:
                spider.logger.warning(f'丢弃{request.to_dict()}，状态码：{response.status}')
                return True

    async def process_exception(self, request, exc, spider):
        if exc.__class__.__name__ in self.retry_exceptions:
            if request.retry < self.max_retry:
                request.retry += 1
                return request
            else:
                spider.logger.warning(f'丢弃{request.to_dict()}，异常：{repr(exc)}')
                return True
