from RabbitSpider.middleware import BaseMiddleware


class TestMiddleware(BaseMiddleware):

    async def process_request(self, request, spider):
        """请求预处理"""
        pass

    async def process_response(self, request, response, spider):
        """响应预处理"""
        pass

    async def process_exception(self, request, exc, spider):
        """异常预处理"""
        pass
