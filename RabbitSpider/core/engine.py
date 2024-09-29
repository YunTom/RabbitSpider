import pickle
import asyncio
from aio_pika import IncomingMessage
from RabbitSpider import Request
from RabbitSpider.utils.control import TaskManager
from RabbitSpider.utils.control import PipelineManager
from RabbitSpider.utils.control import MiddlewareManager
from RabbitSpider.utils.control import FilterManager
from RabbitSpider.utils.exceptions import RabbitExpect
from RabbitSpider.items.item import BaseItem
from RabbitSpider.core.scheduler import Scheduler
from collections.abc import AsyncGenerator, Coroutine, Generator
from aio_pika.exceptions import QueueEmpty, ChannelClosed, ChannelNotFoundEntity


class Engine(object):

    def __init__(self, crawler):
        self.connection = None
        self.channel = None
        self.mode = crawler.mode
        self.spider = crawler.spider
        self.task_count = crawler.task_count
        self.settings = crawler.settings
        self.scheduler = Scheduler(self.settings)
        self.filter = FilterManager(self.settings)
        self.task_manager = TaskManager(self.task_count)
        self.middlewares = MiddlewareManager.create_instance(self.spider,self.settings)
        self.pipelines = PipelineManager.create_instance(self.spider,self.settings)

    async def routing(self, result):
        async def rule(res):
            if isinstance(res, Request):
                if self.filter.request_seen(res):
                    self.spider.logger.info(f'生产数据：{res.to_dict()}')
                    await self.scheduler.producer(self.channel, queue=self.spider.name, body=res.to_dict())
            elif isinstance(res, BaseItem):
                await self.pipelines.process_item(res)

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
            await self.scheduler.queue_purge(self.channel, self.spider.name)
            await self.routing(self.spider.start_requests())
        except Exception as e:
            self.spider.logger.error(f'{e}')
            for task in asyncio.all_tasks():
                task.cancel()

    async def crawl(self):
        while True:
            try:
                incoming_message: IncomingMessage = await self.scheduler.consumer(self.channel, self.spider.name)
            except QueueEmpty:
                if self.task_manager.all_done():
                    await self.scheduler.delete_queue(self.channel, self.spider.name)
                    break
                else:
                    continue
            except ChannelNotFoundEntity:
                break
            except ChannelClosed:
                await asyncio.sleep(1)
                self.spider.logger.warning('rabbitmq重新连接')
                self.connection, self.channel = await self.scheduler.connect()
                continue
            await self.task_manager.semaphore.acquire()
            self.task_manager.create_task(self.deal_resp(incoming_message))

    async def consume(self):
        while True:
            try:
                await self.scheduler.consumer(self.channel, queue=self.spider.name, callback=self.deal_resp,
                                              prefetch=self.task_count)
            except ChannelClosed:
                await asyncio.sleep(1)
                self.spider.logger.warning('rabbitmq重新连接')
                self.connection, self.channel = await self.scheduler.connect()
                continue
            await asyncio.Future()

    async def deal_resp(self, incoming_message: IncomingMessage):
        ret = pickle.loads(incoming_message.body)
        self.spider.logger.info(f'消费数据：{ret}')
        request, response = await self.middlewares.downloader(Request(**ret))
        if response:
            try:
                callback = getattr(self.spider, ret['callback'])
                result = callback(request, response)
                if result:
                    await self.routing(result)
            except Exception as e:
                self.spider.logger.error(f'解析失败：{e}')
                for task in asyncio.all_tasks():
                    task.cancel()
            else:
                await incoming_message.ack()

    async def open(self):
        self.connection, self.channel = await self.scheduler.connect()
        await self.scheduler.create_queue(self.channel, self.spider.name)
        await self.pipelines.open_spider()

    async def close(self):
        await self.pipelines.close_spider()
        await self.channel.close()
        await self.connection.close()

    async def start(self):
        await self.open()
        if self.mode == 'auto':
            await self.produce()
            await self.crawl()
        elif self.mode == 'm':
            await self.produce()
        elif self.mode == 'w':
            await self.consume()
        else:
            raise RabbitExpect('执行模式错误！')
        await self.close()
