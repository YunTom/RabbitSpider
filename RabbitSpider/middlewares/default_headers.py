from RabbitSpider.middlewares import BaseMiddleware


class DefaultHeadersMiddleware(BaseMiddleware):
    def __init__(self, spider):
        super().__init__(spider)
        self.default_headers = spider.settings.get('DEFAULT_HEADERS')

    async def process_request(self, request, spider):
        if not request.headers:
            request.headers = self.default_headers
