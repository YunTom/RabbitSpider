from RabbitSpider.middlewares import BaseMiddleware


class AllowHttpCodeMiddleware(BaseMiddleware):
    def __init__(self, spider, settings):
        super().__init__(spider, settings)
        self.allow_http_code = settings.getlist('ALLOW_HTTP_CODES')

    async def process_response(self, request, response, spider):
        if response.status not in self.allow_http_code:
            spider.logger.error(f'{request.to_dict()}，不允许的状态码：{response.status}')
            return True
