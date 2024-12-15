from typing import AsyncGenerator
from RabbitSpider.utils.log import Logger
from RabbitSpider import Request, Response, event, BaseItem
from RabbitSpider.utils.control import SettingManager
from curl_cffi.requests import AsyncSession


class Spider(object):
    name: str
    custom_settings: dict = {}

    def __init__(self, crawler):
        self.logger: Logger = crawler.logger
        self.session: AsyncSession = crawler.session
        self.settings: SettingManager = crawler.settings
        crawler.subscriber.subscribe(self.spider_opened, event.spider_opened)
        crawler.subscriber.subscribe(self.spider_closed, event.spider_closed)
        crawler.subscriber.subscribe(self.spider_error, event.spider_error)
        crawler.subscriber.subscribe(self.request_received, event.request_received)
        crawler.subscriber.subscribe(self.response_received, event.response_received)
        crawler.subscriber.subscribe(self.item_scraped, event.item_scraped)

    async def start_requests(self) -> AsyncGenerator[Request] | None:
        """初始请求"""
        raise NotImplementedError

    async def parse(self, request: Request, response: Response) -> AsyncGenerator[Request | BaseItem] | None:
        """默认回调"""
        pass

    async def spider_opened(self, spider) -> None:
        """爬虫启动时触发"""
        pass

    async def spider_closed(self, spider) -> None:
        """爬虫关闭时触发"""
        pass

    async def spider_error(self, spider, error) -> None:
        """爬虫异常时触发"""
        pass

    async def request_received(self, spider, request) -> None:
        """发起请求时触发"""
        pass

    async def response_received(self, spider, response) -> None:
        """获取到响应时触发"""
        pass

    async def item_scraped(self, spider, item) -> None:
        """生成item时触发"""
        pass
