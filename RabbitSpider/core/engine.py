import pickle
import asyncio
from asyncio import CancelledError
from aio_pika import IncomingMessage
from RabbitSpider import Request
from RabbitSpider import Response
from RabbitSpider.utils.control import TaskManager
from RabbitSpider.utils.control import SettingManager
from RabbitSpider.utils.control import PipelineManager
from RabbitSpider.utils.control import MiddlewareManager
from RabbitSpider.utils.control import FilterManager
from RabbitSpider.utils.subscriber import Subscriber
from RabbitSpider.utils.event import *
from RabbitSpider.utils.exceptions import RabbitExpect
from RabbitSpider.utils.log import Logger
from RabbitSpider.items.item import BaseItem
from RabbitSpider.core.scheduler import Scheduler
from collections.abc import AsyncGenerator, Coroutine, Generator
from aio_pika.exceptions import QueueEmpty, ChannelClosed, ChannelNotFoundEntity


class Engine(object):
    name: str
    custom_settings: dict = {}

    def __init__(self, task_count):
        self.session = None
        self.__connection = None
        self.__channel = None
        self.__task_count = task_count
        self.settings = SettingManager(self.custom_settings)
        self.__scheduler = Scheduler(self.settings)
        self.__filter = FilterManager(self.settings)
        self.__task_manager = TaskManager(self.__task_count)
        self.__middlewares = MiddlewareManager.create_instance(self)
        self.__pipelines = PipelineManager.create_instance(self)
        self.logger = Logger(self.settings, self.name)
        self.subscriber = Subscriber.create_instance()
        self.subscriber.subscribe(self.spider_opened, spider_opened)
        self.subscriber.subscribe(self.spider_closed, spider_closed)
        self.subscriber.subscribe(self.spider_error, spider_error)

    async def start_requests(self):
        """初始请求"""
        raise NotImplementedError

    async def parse(self, request: Request, response: Response):
        """默认回调"""
        pass

    def spider_opened(self, *args, **kwargs):
        pass

    def spider_closed(self, *args, **kwargs):
        pass

    def spider_error(self, *args, **kwargs):
        pass

    async def routing(self, result):
        async def rule(res):
            if isinstance(res, Request):
                if self.__filter.request_seen(res):
                    self.logger.info(f'生产数据：{res.to_dict()}')
                    await self.__scheduler.producer(self.__channel, queue=self.name, body=res.to_dict())
            elif isinstance(res, BaseItem):
                await self.__pipelines.process_item(res)

        if isinstance(result, AsyncGenerator):
            async for r in result:
                await rule(r)
        elif isinstance(result, Generator):
            for r in result:
                await rule(r)
        elif isinstance(result, Coroutine):
            r = await result
            await rule(r)
        elif isinstance(result, Request):
            await rule(result)
        elif result is None:
            pass
        else:
            raise RabbitExpect('回调函数返回类型错误！')

    async def produce(self):
        try:
            await self.__scheduler.queue_purge(self.__channel, self.name)
            await self.routing(self.start_requests())
        except Exception as e:
            self.logger.error(f'{e}')
            for task in asyncio.all_tasks():
                task.cancel()

    async def crawl(self):
        while True:
            try:
                incoming_message: IncomingMessage = await self.__scheduler.consumer(self.__channel, self.name)
            except QueueEmpty:
                if self.__task_manager.all_done():
                    await self.__scheduler.delete_queue(self.__channel, self.name)
                    break
                else:
                    continue
            except ChannelNotFoundEntity:
                break
            except ChannelClosed:
                await asyncio.sleep(1)
                self.logger.warning('rabbitmq重新连接')
                self.__connection, self.__channel = await self.__scheduler.connect()
                continue
            await self.__task_manager.semaphore.acquire()
            self.__task_manager.create_task(self.deal_resp(incoming_message))

    async def consume(self):
        while True:
            try:
                await self.__scheduler.consumer(self.__channel, queue=self.name, callback=self.deal_resp,
                                                prefetch=self.__task_count)
            except ChannelClosed:
                await asyncio.sleep(1)
                self.logger.warning('rabbitmq重新连接')
                self.__connection, self.__channel = await self.__scheduler.connect()
                continue
            await asyncio.Future()

    async def deal_resp(self, incoming_message: IncomingMessage):
        ret = pickle.loads(incoming_message.body)
        self.logger.info(f'消费数据：{ret}')
        request, response = await self.__middlewares.downloader(Request(**ret))
        if response:
            try:
                callback = getattr(self, ret['callback'])
                result = callback(request, response)
                if result:
                    await self.routing(result)
            except Exception as e:
                self.logger.error(f'解析失败：{e}')
                for task in asyncio.all_tasks():
                    task.cancel()
            else:
                await incoming_message.ack()

    async def __open_spider(self):
        self.__connection, self.__channel = await self.__scheduler.connect()
        self.session = await self.__middlewares.download.new_session()
        await self.__scheduler.create_queue(self.__channel, self.name)
        await self.__pipelines.open_spider()
        self.subscriber.notify(spider_opened, self.spider_opened, self)

    async def __close_spider(self):
        await self.__pipelines.close_spider()
        await self.__channel.close()
        await self.__connection.close()
        await self.__middlewares.download.exit(self.session)
        self.subscriber.notify(spider_closed, self.spider_closed, self)

    async def run(self, mode):
        try:
            self.logger.info(f'{self.name}任务开始')
            await self.__open_spider()
            if mode == 'auto':
                await self.produce()
                await self.crawl()
            elif mode == 'm':
                await self.produce()
            elif mode == 'w':
                await self.consume()
            else:
                raise RabbitExpect('执行模式错误！')
            await self.__close_spider()
            self.logger.info(f'{self.name}任务结束')
        except CancelledError as exc:
            self.subscriber.notify(spider_error, self.spider_error, exc)
        except Exception as exc:
            self.subscriber.notify(spider_error, self.spider_error, exc)
