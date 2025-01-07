from asyncio import CancelledError
from typing import AsyncGenerator, Union
from curl_cffi.requests import AsyncSession
from RabbitSpider.utils import event
from RabbitSpider import Request, Response, BaseItem
from RabbitSpider.utils.subscriber import Subscriber


class Spider(object):
    name: str

    def __init__(self):
        self.subscriber = Subscriber()
        self.session = AsyncSession(verify=False)
        self.subscriber.subscribe(self.spider_opened, event.spider_opened)
        self.subscriber.subscribe(self.spider_closed, event.spider_closed)
        self.subscriber.subscribe(self.spider_error, event.spider_error)
        self.subscriber.subscribe(self.request_received, event.request_received)
        self.subscriber.subscribe(self.response_received, event.response_received)
        self.subscriber.subscribe(self.item_scraped, event.item_scraped)

    async def start_requests(self) -> AsyncGenerator[Request, None]:
        """初始请求"""
        raise NotImplementedError

    async def parse(self, request: Request, response: Response) -> AsyncGenerator[Union[Request, BaseItem, None], None]:
        """默认回调"""
        pass

    async def spider_opened(self) -> None:
        """爬虫启动时触发"""
        pass

    async def spider_closed(self) -> None:
        """爬虫关闭时触发"""
        pass

    async def spider_error(self, error: Exception | CancelledError) -> None:
        """爬虫异常时触发"""
        pass

    async def request_received(self, request: Request) -> None:
        """发起请求时触发"""
        pass

    async def response_received(self, response: Response) -> None:
        """获取到响应时触发"""
        pass

    async def item_scraped(self, item: BaseItem) -> None:
        """生成item时触发"""
        pass
