from typing import TYPE_CHECKING, Literal

from RabbitSpider import Request, Response, settings, logger
from RabbitSpider.interceptor import Signal, SignalDispatcher

if TYPE_CHECKING:
    from RabbitSpider.spider import BaseSpider


class AllowHttpCode(SignalDispatcher):
    def __init__(self) -> None:
        self.allow_http_code = settings.getlist('ALLOW_HTTP_CODES')

    async def response_received(
            self,
            spider: "BaseSpider",
            request: Request,
            response: Response,
    ) -> Literal[Signal.response_stop] | None:
        if response.status_code not in self.allow_http_code:
            logger.error(f'{request.to_dict()}，不允许的状态码：{response.status_code}', spider.name)
            await spider.subscriber.notify(Signal.request_dropped, spider, request=request)
            return Signal.response_stop
