import pickle
import asyncio
from asyncio import CancelledError
from aio_pika import IncomingMessage
from RabbitSpider.utils import event
from RabbitSpider.utils.log import Logger
from RabbitSpider import Request, BaseItem
from RabbitSpider.exceptions import RabbitExpect
from RabbitSpider.core.scheduler import Scheduler
from typing import AsyncGenerator, Coroutine, Generator
from RabbitSpider.utils.control import SettingManager, MiddlewareManager, FilterManager, PipelineManager, TaskManager


class Engine(object):

    def __init__(self, mode, task_count):
        self.mode: str = mode
        self.task_count: int = task_count
        self.settings = SettingManager()
        self.logger = Logger(self.settings)
        self.scheduler = Scheduler(self.settings)
        self.filter = FilterManager(self.settings)
        self.pipeline = PipelineManager(self.settings)
        self.middlewares = MiddlewareManager(self.settings)
        self.task_manager: TaskManager = TaskManager(task_count)
        loop = asyncio.get_running_loop()
        loop.set_exception_handler(self.custom_exception_handler)

    def custom_exception_handler(self, _loop, context):
        self.logger.error(f"Exception type: {context['exception'].__class__.__name__} : {context['exception']}")
        try:
            for task in asyncio.all_tasks():
                task.cancel()
        except RuntimeError:
            pass

    async def __aenter__(self):
        await self.scheduler.connect()
        await self.pipeline.open_spider()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.scheduler.close()
        await self.pipeline.close_spider()

    async def routing(self, spider, result):
        async def rule(res):
            if isinstance(res, Request):
                if self.filter.request_seen(res):
                    self.logger.info(f'生产数据：{res.to_dict()}', spider.name)
                    await self.scheduler.producer(queue=spider.name, body=res.to_dict())
            elif isinstance(res, BaseItem):
                await spider.subscriber.notify(event.item_scraped, res)
                await self.pipeline.process_item(res, spider)
            elif res is None:
                pass
            else:
                raise TypeError('回调函数返回类型错误！')

        if isinstance(result, AsyncGenerator):
            async for r in result:
                await rule(r)
        elif isinstance(result, Generator):
            for r in result:
                await rule(r)
        elif isinstance(result, Coroutine):
            await rule(await result)
        elif isinstance(result, Request):
            await rule(result)
        elif result is None:
            pass
        else:
            raise TypeError('回调函数返回类型错误！')

    async def produce(self, spider):
        await self.scheduler.create_queue(spider.name)
        await self.scheduler.queue_purge(spider.name)
        await self.routing(spider, spider.start_requests())

    async def crawl(self, spider):
        while True:
            incoming_message: IncomingMessage = await self.scheduler.consumer(spider)
            if incoming_message:
                await self.task_manager.semaphore.acquire()
                self.task_manager.create_task(self.deal_resp(spider, incoming_message))
            else:
                if self.task_manager.all_done():
                    await self.scheduler.delete_queue(spider.name)
                    break

    async def consume(self, spider):
        await self.scheduler.consumer(spider, callback=self.deal_resp,
                                      prefetch=self.task_count)
        await asyncio.Future()

    async def deal_resp(self, spider, incoming_message: IncomingMessage):
        request = Request(**pickle.loads(incoming_message.body))
        self.logger.info(f'消费数据：{request.to_dict()}', spider.name)
        await spider.subscriber.notify(event.request_received, request)
        request, response = await self.middlewares.send(spider, request)
        if response:
            await spider.subscriber.notify(event.response_received, response)
            result = getattr(spider, request.callback)(request, response)
            result and await self.routing(spider, result)
        elif request:
            await self.routing(spider, request)
        await incoming_message.ack()

    async def start(self, spider):
        self.logger.info(f'任务{spider.name}启动')
        await spider.subscriber.notify(event.spider_opened)
        try:
            if self.mode == 'auto':
                await self.produce(spider)
                await self.crawl(spider)
            elif self.mode == 'm':
                await self.produce(spider)
            elif self.mode == 'w':
                await self.consume(spider)
            else:
                raise RabbitExpect('执行模式错误！')
        except CancelledError as exc:
            self.logger.error(f'任务{spider.name}异常: {exc.__class__.__name__}')
            await spider.subscriber.notify(event.spider_error, exc)
        except Exception as exc:
            self.logger.error(f'任务{spider.name}异常: {exc.__class__.__name__}')
            await spider.subscriber.notify(event.spider_error, exc)
        else:
            await spider.subscriber.notify(event.spider_closed)
            self.logger.info(f'任务{spider.name}结束')
