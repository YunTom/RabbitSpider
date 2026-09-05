from collections import defaultdict
from typing import Any, Awaitable, Callable, Iterable, TypeVar, cast
from RabbitSpider import Request, Response, BaseItem
from RabbitSpider.interceptor import Signal, SignalDispatcher

T_SignalDispatcher = TypeVar('T_SignalDispatcher', bound=SignalDispatcher)
SignalResult = bool | Signal | Request | Response | None
SignalCallback = Callable[..., Awaitable[SignalResult]]


class Subscriber:
    def __init__(self) -> None:
        self._subscriber: dict[Signal, list[SignalCallback]] = defaultdict(list)
        self._receivers: dict[type[SignalDispatcher], SignalDispatcher] = {}

    def subscribe(self, receiver: type[T_SignalDispatcher]) -> None:
        if receiver in self._receivers:
            return

        dispatcher = receiver()
        self._receivers[receiver] = dispatcher
        for signal in cast(Iterable[Signal], Signal):
            callback = getattr(dispatcher, signal.value, None)
            if callback:
                self._subscriber[signal].append(callback)

    def unsubscribe(self, receiver: type[T_SignalDispatcher]) -> None:
        dispatcher = self._receivers.pop(receiver, None)
        for signal in cast(Iterable[Signal], Signal):
            callback = getattr(dispatcher, signal.value, None)
            if callback:
                self._remove_callback(signal, callback)

    def _remove_callback(self, signal: Signal, callback: SignalCallback) -> None:
        if signal in self._subscriber:
            self._subscriber[signal] = [
                cb for cb in self._subscriber[signal] if cb != callback
            ]

    async def notify(
            self,
            signal: Signal,
            spider: Any,
            request: Request | None = None,
            response: Response | None = None,
            item: BaseItem | None = None,
            exc: Exception | None = None,
    ) -> SignalResult:
        """
        异步触发信号，自动分发参数并返回第一个非 None 的结果（如适用）。
        """
        if not isinstance(signal, Signal):
            raise TypeError(f"signal 必须是 Signal，实际为 {type(signal).__name__}")

        callbacks = self._subscriber.get(signal, [])
        # 信号对应参数映射
        param_map = {
            Signal.spider_opened: (spider,),
            Signal.spider_closed: (spider,),
            Signal.spider_error: (spider, exc),
            Signal.request_scheduled: (spider, request),
            Signal.request_received: (spider, request),
            Signal.request_stop: (spider, request),
            Signal.request_dropped: (spider, request),
            Signal.request_error: (spider, request, exc),
            Signal.response_received: (spider, request, response),
            Signal.response_stop: (spider, request, response),
            Signal.item_scraped: (spider, item),
        }

        for cb in callbacks:
            result = await cb(*param_map.get(signal, ()))
            # 对于返回值信号，遇到非 None 就返回
            if signal in {
                Signal.request_scheduled,
                Signal.request_received,
                Signal.request_error,
                Signal.response_received,
                Signal.item_scraped,
                Signal.spider_error
            } and result is not None:
                return result
        return None
