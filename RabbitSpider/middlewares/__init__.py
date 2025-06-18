from RabbitSpider import Request
from RabbitSpider import Response
from RabbitSpider.utils.log import Logger
from RabbitSpider.utils.control import SettingManager


class BaseMiddleware(object):
    def __init__(self, settings):
        self.logger = Logger(settings)
        self.settings: SettingManager = settings

    async def process_request(self, request, spider) -> None | Request | Response:
        """请求预处理"""
        pass

    async def process_response(self, request, response, spider) -> Request | Response:
        """响应预处理"""
        pass

    async def process_exception(self, request, exc, spider) -> None | Request | Response:
        """异常预处理"""
        pass
