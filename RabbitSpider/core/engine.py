import pickle
import asyncio
from aio_pika import IncomingMessage
from RabbitSpider.utils import event
from RabbitSpider import Request, BaseItem
from RabbitSpider.exceptions import RabbitExpect
from typing import AsyncGenerator, Coroutine, Generator


class Engine(object):

    def __init__(self, crawler):
        self.mode = crawler.mode
        self.spider = crawler.spider
        self.subscriber = crawler.subscriber
        self.task_count = crawler.task_count
        self.scheduler = crawler.scheduler
        self.filter = crawler.filter
        self.task_manager = crawler.task_manager
        self.middlewares = crawler.middlewares
        self.pipeline = crawler.pipeline
        self.logger = crawler.logger

    async def __aenter__(self):
        await self.scheduler.connect()
        await self.scheduler.create_queue(self.spider.name)
        await self.pipeline.open_spider()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.scheduler.close()
        await self.pipeline.close_spider()

    async def routing(self, result):
        async def rule(res):
            if isinstance(res, Request):
                if self.filter.request_seen(res):
                    self.logger.info(f'生产数据：{res.to_dict()}')
                    await self.scheduler.producer(queue=self.spider.name, body=res.to_dict())
            elif isinstance(res, BaseItem):
                await self.subscriber.notify(event.item_scraped, res)
                await self.pipeline.process_item(res)
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
            r = await result
            await rule(r)
        elif isinstance(result, Request):
            await rule(result)
        elif result is None:
            pass
        else:
            raise TypeError('回调函数返回类型错误！')

    async def produce(self):
        await self.scheduler.queue_purge(self.spider.name)
        await self.routing(self.spider.start_requests())

    async def crawl(self):
        while True:
            incoming_message: IncomingMessage = await self.scheduler.consumer(self.spider.name)
            if incoming_message:
                await self.task_manager.semaphore.acquire()
                self.task_manager.create_task(self.deal_resp(incoming_message))
            else:
                if self.task_manager.all_done():
                    await self.scheduler.delete_queue(self.spider.name)
                    break
                else:
                    continue

    async def consume(self):
        await self.scheduler.consumer(queue=self.spider.name, callback=self.deal_resp,
                                      prefetch=self.task_count)
        await asyncio.Future()

    async def deal_resp(self, incoming_message: IncomingMessage):
        request = Request(**pickle.loads(incoming_message.body))
        await self.subscriber.notify(event.request_received, request)
        request, response = await self.middlewares.send(request)
        if response:
            await self.subscriber.notify(event.response_received, response)
            result = getattr(self.spider, request.callback)(request, response)
            result and await self.routing(result)
        elif request:
            await self.routing(request)
        await incoming_message.ack()

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
