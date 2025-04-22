from RabbitSpider.middlewares import BaseMiddleware


class AllowHttpCodeMiddleware(BaseMiddleware):
    def __init__(self, settings):
        super().__init__(settings)
        self.allow_http_code = settings.getlist('ALLOW_HTTP_CODES')

    async def process_response(self, request, response, spider):
        if response.status_code not in self.allow_http_code:
            self.logger.error(f'{request.to_dict()}，不允许的状态码：{response.status_code}',spider.name)
            return True
