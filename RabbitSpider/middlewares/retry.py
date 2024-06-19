from RabbitSpider.middlewares import BaseMiddleware


class RetryMiddleware(BaseMiddleware):
    def __init__(self, spider):
        super().__init__(spider)
        self.retry_http_code = spider.settings.get('RETRY_HTTP_CODE')
        self.retry_exceptions = spider.settings.get('RETRY_EXCEPTIONS')
        self.max_retry = spider.settings.get('MAX_RETRY')

    async def process_response(self, request, response, spider):
        if response.status in self.retry_http_code:
            if request.retry < self.max_retry:
                request.retry += 1
                return request
            else:
                spider.logger.warning(f'丢弃{request.model_dump()}，状态码：{response.status}')
        return True

    async def process_exception(self, request, exc, spider):
        if exc.name in self.retry_exceptions:
            if request.retry < self.max_retry:
                request.retry += 1
                return request
            else:
                spider.logger.warning(f'丢弃{request.model_dump()}，异常：{exc}')
        return True
