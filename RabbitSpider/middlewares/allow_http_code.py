from RabbitSpider.middlewares import BaseMiddleware
from RabbitSpider.utils.exceptions import RabbitExpect


class AllowHttpCodeMiddleware(BaseMiddleware):
    def __init__(self, spider):
        super().__init__(spider)
        self.allow_http_code = spider.settings.getlist('ALLOW_HTTP_CODES')

    async def process_response(self, request, response, spider):
        if response.status in self.allow_http_code:
            return response
        else:
            raise RabbitExpect(f'{request.model_dump()}，不允许的状态码：{response.status}')
