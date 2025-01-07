from RabbitSpider.middlewares import BaseMiddleware


class RetryMiddleware(BaseMiddleware):
    def __init__(self, settings):
        super().__init__(settings)
        self.retry_http_code = settings.getlist('RETRY_HTTP_CODES')
        self.retry_exceptions = settings.getlist('RETRY_EXCEPTIONS')
        self.max_retry = settings.get('MAX_RETRY')

    async def process_response(self, request, response, spider):
        if response.status in self.retry_http_code:
            if request.retry_times < self.max_retry:
                request.retry_times += 1
                return request
            else:
                self.logger.warning(f'丢弃{request.to_dict()}，状态码：{response.status}',spider.name)
                return True

    async def process_exception(self, request, exc, spider):
        if exc.__class__.__name__ in self.retry_exceptions:
            if request.retry_times < self.max_retry:
                request.retry_times += 1
                return request
            else:
                self.logger.warning(f'丢弃{request.to_dict()}，异常：{repr(exc)}',spider.name)
                return True
