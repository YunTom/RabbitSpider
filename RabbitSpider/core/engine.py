import asyncio
import inspect
from typing import Any
from types import TracebackType
from RabbitSpider.spider import BaseSpider
from RabbitSpider import Request, BaseItem
from RabbitSpider.interceptor import Signal
from RabbitSpider.core.scheduler import Scheduler
from RabbitSpider import settings, logger, Response


class Engine:

    def __init__(self, spider: BaseSpider) -> None:
        self.spider = spider
        self.scheduler = Scheduler()
        self.mode = settings.get('MODE')
        self.download = settings.get('DOWNLOADER')
        self.task_count = settings.get('TASK_COUNT')

    async def __aenter__(self) -> "Engine":
        await self.scheduler.connect()
        return self

    async def __aexit__(
            self,
            exc_type: type[BaseException] | None,
            exc_val: BaseException | None,
            exc_tb: TracebackType | None,
    ) -> None:
        await self.scheduler.close()

    async def dispatch_result(self, result: Any) -> None:
        if result is None:
            return
        if inspect.isasyncgen(result):
            async for r in result:
                await self._handle_result(r)
            return
        if asyncio.iscoroutine(result):
            result = await result
        await self._handle_result(result)

    async def _handle_result(self, res: Any) -> None:
        if res is None:
            return
        if isinstance(res, Request):
            blocked = await self.spider.subscriber.notify(
                Signal.request_scheduled,
                self.spider,
                request=res,
            )
            if not blocked:
                logger.info(f"生产数据：{res.to_dict()}", self.spider.name)

                await self.scheduler.producer(
                    queue_name=self.spider.name,
                    body=res.to_dict(),
                )
            return
        if isinstance(res, BaseItem):
            await self.spider.subscriber.notify(
                Signal.item_scraped,
                self.spider,
                item=res,
            )
            return
        raise TypeError(f"回调函数返回类型错误: {type(res)}")

    async def produce(self) -> None:
        await self.scheduler.create_queue(self.spider.name)
        await self.scheduler.queue_purge(self.spider.name)
        await self.dispatch_result(self.spider.start_requests())

    async def consume(self, auto_exit: bool) -> None:
        await self.scheduler.consumer(self.spider, callback=self.process_message,
                                      prefetch=self.task_count)
        if not auto_exit:
            await asyncio.Future()
            return
        empty_count = 0
        while True:
            await asyncio.sleep(30)
            if self.scheduler.active_task_count == 0:
                if await self.scheduler.is_queue_empty(self.spider.name):
                    empty_count += 1
                    if empty_count >= 3:
                        break
                else:
                    empty_count = 0
            else:
                empty_count = 0

    async def process_message(self, message: dict[str, Any]) -> None:
        request = Request(**message)
        try:
            req_event = await self.spider.subscriber.notify(
                Signal.request_received,
                self.spider,
                request=request,
            )
            if isinstance(req_event, Request):
                request = req_event
            if req_event == Signal.request_stop:
                await self.spider.subscriber.notify(
                    Signal.request_stop,
                    self.spider,
                    request=request,
                )
                return
            logger.info(f"消费数据：{request.to_dict()}", self.spider.name)

            async with self.download() as downloader:
                try:
                    response = await downloader.fetch(request.to_dict())
                except Exception as exc:
                    retry_req = await self.spider.subscriber.notify(
                        Signal.request_error,
                        self.spider,
                        request=request,
                        exc=exc,
                    )
                    if isinstance(retry_req, Request):
                        await self.dispatch_result(retry_req)
                else:
                    await self._handle_response(request, response)
        except Exception as exc:
            await self.spider.subscriber.notify(
                Signal.spider_error,
                self.spider,
                exc=exc,
            )

    async def _handle_response(self, request: Request, response: Response) -> None:
        event = await self.spider.subscriber.notify(
            Signal.response_received,
            self.spider,
            request=request,
            response=response,
        )

        if isinstance(event, Response):
            result = getattr(self.spider, request.callback)(
                request,
                event,
            )
        elif isinstance(event, Request):
            await self.dispatch_result(event)
            return
        elif event == Signal.response_stop:
            await self.spider.subscriber.notify(
                Signal.response_stop,
                self.spider,
                request=request,
                response=response,
            )
            return

        else:
            result = getattr(self.spider, request.callback)(
                request,
                response,
            )
        await self.dispatch_result(result)

    async def run(self) -> None:
        logger.info(f'任务启动', self.spider.name)
        await self.spider.subscriber.notify(Signal.spider_opened, self.spider)
        if self.mode == 'auto':
            await self.produce()
            await self.consume(auto_exit=True)
        elif self.mode == 'm':
            await self.produce()
        elif self.mode == 'w':
            await self.consume(auto_exit=False)
        else:
            raise ValueError('模式错误')
        await self.spider.subscriber.notify(Signal.spider_closed, self.spider)
        logger.info(f'任务结束', self.spider.name)
