import pickle
import asyncio
from aio_pika import IncomingMessage
from RabbitSpider import Request
from RabbitSpider.items.item import BaseItem
from RabbitSpider.utils import event
from RabbitSpider.utils.exceptions import RabbitExpect
from collections.abc import AsyncGenerator, Coroutine, Generator
from aio_pika.exceptions import QueueEmpty, ChannelClosed, ChannelNotFoundEntity


class Engine(object):

    def __init__(self, crawler):
        self.connection = None
        self.channel = None
        self.mode = crawler.mode
        self.spider = crawler.spider
        self.subscriber = crawler.subscriber
        self.task_count = crawler.task_count
        self.scheduler = crawler.scheduler
        self.filter = crawler.filter
        self.task_manager = crawler.task_manager
        self.download = crawler.download

    async def __aenter__(self):
        self.connection, self.channel = await self.scheduler.connect()
        await self.scheduler.create_queue(self.channel, self.spider.name)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.channel.close()
        await self.connection.close()

    async def routing(self, result):
        async def rule(res):
            if isinstance(res, Request):
                if self.filter.request_seen(res):
                    self.spider.logger.info(f'生产数据：{res.to_dict()}')
                    await self.scheduler.producer(self.channel, queue=self.spider.name, body=res.to_dict())
            elif isinstance(res, BaseItem):
                self.subscriber.notify(event.spider_item, res, self.spider)

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
        request, response = await self.download.send(Request(**ret))
        if response:
            try:
                callback = getattr(self.spider, ret['callback'])
                result = await callback(request, response)
                if result:
                    await self.routing(result)
            except Exception as e:
                self.spider.logger.error(f'解析失败：{e}')
                for task in asyncio.all_tasks():
                    task.cancel()
            else:
                await incoming_message.ack()
        elif request:
            await self.routing(request)

    async def start(self):
        if self.mode == 'auto':
            await self.produce()
            await self.crawl()
        elif self.mode == 'm':
            await self.produce()
        elif self.mode == 'w':
            await self.consume()
        else:
            raise RabbitExpect('执行模式错误！')
