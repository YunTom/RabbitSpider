from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, cast
from collections.abc import AsyncIterator
from RabbitSpider import Request, Response, BaseItem
from RabbitSpider.utils.subscriber import Subscriber
from RabbitSpider.interceptor.redis_filter import RedisFilter
from RabbitSpider.interceptor.retry_download import RetryDownload
from RabbitSpider.interceptor.download_delay import DownloadDelay
from RabbitSpider.interceptor.allow_http_code import AllowHttpCode


class BaseSpider(ABC):
    name: str
    custom_settings: dict = {}

    def __init__(self) -> None:
        self.subscriber = Subscriber()
        self.subscriber.subscribe(RedisFilter)
        self.subscriber.subscribe(DownloadDelay)
        self.subscriber.subscribe(RetryDownload)
        self.subscriber.subscribe(AllowHttpCode)

    @abstractmethod
    async def start_requests(self) -> AsyncIterator[Request]:
        """初始请求"""
        if TYPE_CHECKING:
            yield cast(Request, None)

    @abstractmethod
    async def parse(
            self,
            request: Request,
            response: Response,
    ) -> AsyncIterator[Request | BaseItem | None]:
        """默认回调"""
        if TYPE_CHECKING:
            yield None
