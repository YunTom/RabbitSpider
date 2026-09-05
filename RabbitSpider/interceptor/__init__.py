from enum import Enum
from typing import TYPE_CHECKING, Literal
from RabbitSpider import Request, Response, BaseItem

if TYPE_CHECKING:
    from RabbitSpider.spider import BaseSpider


class Signal(str, Enum):
    # 爬虫启动时触发
    spider_opened = 'spider_opened'
    # 请求对象入队列时触发
    request_scheduled = 'request_scheduled'
    # 发起请求时触发
    request_received = 'request_received'
    # 请求被丢弃时触发
    request_dropped = 'request_dropped'
    # 请求异常时触发
    request_error = 'request_error'
    # 终止请求信号
    request_stop = 'request_stop'
    # 获取到响应时触发
    response_received = 'response_received'
    # 终止响应信号
    response_stop = 'response_stop'
    # 生成item时触发
    item_scraped = 'item_scraped'
    # 爬虫异常时触发
    spider_error = 'spider_error'
    # 爬虫关闭时触发
    spider_closed = 'spider_closed'


class SignalDispatcher(object):

    async def spider_opened(self, spider: "BaseSpider") -> None:
        pass

    async def request_scheduled(self, spider: "BaseSpider", request: Request) -> bool | None:
        pass

    async def request_received(
            self,
            spider: "BaseSpider",
            request: Request,
    ) -> Request | Literal[Signal.request_stop] | None:
        pass

    async def request_stop(self, spider: "BaseSpider", request: Request) -> None:
        pass

    async def request_dropped(self, spider: "BaseSpider", request: Request) -> None:
        pass

    async def request_error(
            self,
            spider: "BaseSpider",
            request: Request,
            exc: Exception,
    ) -> Request | None:
        pass

    async def response_received(
            self,
            spider: "BaseSpider",
            request: Request,
            response: Response,
    ) -> Request | Response | Literal[Signal.response_stop] | None:
        pass

    async def response_stop(
            self,
            spider: "BaseSpider",
            request: Request,
            response: Response,
    ) -> None:
        pass

    async def item_scraped(self, spider: "BaseSpider", item: BaseItem) -> None:
        pass

    async def spider_error(self, spider: "BaseSpider", exc: Exception) -> None:
        raise exc

    async def spider_closed(self, spider: "BaseSpider") -> None:
        pass
