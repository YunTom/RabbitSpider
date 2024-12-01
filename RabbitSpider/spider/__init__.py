from RabbitSpider import Request, Response
from RabbitSpider.utils import event
from RabbitSpider.utils.log import Logger
from RabbitSpider.utils.control import SettingManager
from curl_cffi.requests import AsyncSession


class Spider(object):
    name: str
    custom_settings: dict = {}

    def __init__(self, crawler):
        self.session: AsyncSession = crawler.session
        self.logger: Logger = crawler.logger
        self.settings: SettingManager = crawler.settings
        crawler.subscriber.subscribe(self.spider_opened, event.spider_opened)
        crawler.subscriber.subscribe(self.spider_closed, event.spider_closed)
        crawler.subscriber.subscribe(self.spider_error, event.spider_error)

    async def start_requests(self):
        """初始请求"""
        raise NotImplementedError

    async def parse(self, request: Request, response: Response):
        """默认回调"""
        pass

    async def spider_opened(self, *args, **kwargs):
        pass

    async def spider_closed(self, *args, **kwargs):
        pass

    async def spider_error(self, *args, **kwargs):
        pass
