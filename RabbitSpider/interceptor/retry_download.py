from typing import TYPE_CHECKING, Literal
from RabbitSpider import Request, Response, settings, logger
from RabbitSpider.interceptor import Signal, SignalDispatcher

if TYPE_CHECKING:
    from RabbitSpider.spider import BaseSpider


class RetryDownload(SignalDispatcher):
    def __init__(self) -> None:
        self.retry_http_code = settings.getlist('RETRY_HTTP_CODES')
        self.retry_exceptions = settings.getlist('RETRY_EXCEPTIONS')
        self.max_retry = settings.get('MAX_RETRY')

    async def response_received(
            self,
            spider: "BaseSpider",
            request: Request,
            response: Response,
    ) -> Request | Literal[Signal.response_stop] | None:
        if response.status_code in self.retry_http_code:
            if request.retry_times < self.max_retry:
                request.retry_times += 1
                return request
            else:
                logger.warning(f'丢弃{request.to_dict()}，状态码：{response.status_code}', spider.name)
                await spider.subscriber.notify(Signal.request_dropped, spider, request=request)
                return Signal.response_stop

    async def request_error(
            self,
            spider: "BaseSpider",
            request: Request,
            exc: Exception,
    ) -> Request | None:
        if exc.__class__.__name__ in self.retry_exceptions:
            if request.retry_times < self.max_retry:
                request.retry_times += 1
                return request
            else:
                logger.warning(f'丢弃{request.to_dict()}，异常：{repr(exc)}', spider.name)
                await spider.subscriber.notify(Signal.request_dropped, spider, request=request)
                return None
        else:
            raise exc
