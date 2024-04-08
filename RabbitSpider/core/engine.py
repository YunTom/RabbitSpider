import asyncio
import os
import pickle
import sys
from loguru import logger
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator, Coroutine
from traceback import print_exc
from typing import Optional
from aio_pika.abc import AbstractIncomingMessage
from RabbitSpider.core.download import Download
from RabbitSpider.core.scheduler import Scheduler
from aio_pika.exceptions import QueueEmpty, ChannelClosed
from RabbitSpider.utils.control import SettingManager
from RabbitSpider.utils.dupefilter import RFPDupeFilter
from RabbitSpider.http.request import Request
from RabbitSpider.utils.control import TaskManager
from RabbitSpider.utils.expections import RabbitExpect


class Engine(ABC):
    def __init__(self, sync):
        self._filter = None
        self._scheduler = None
        self._connection = None
        self._channel = None
        self._sync = sync
        self.download = Download()
        self.settings = SettingManager()
        self.queue = os.path.basename(sys.argv[0])
        self.allow_status_code: list = [200]
        self.max_retry: int = self.settings.get('MAX_RETRY')
        self.task_manager = TaskManager(self._sync)

    async def start_spider(self):
        await self._scheduler.create_queue(self._channel, self.queue)
        start_request = self.start_requests()
        await self.routing(start_request)

    @abstractmethod
    async def start_requests(self):
        """初始请求"""
        pass

    @abstractmethod
    async def parse(self, request, response):
        """默认回调"""
        pass

    @abstractmethod
    async def save_item(self, item: dict):
        """入库逻辑"""
        pass

    def before_request(self, ret):
        """请求前"""
        return ret

    async def routing(self, result):
        if isinstance(result, AsyncGenerator):
            async for req in result:
                if isinstance(req, Request):
                    ret = pickle.dumps(req.model_dump())
                    if req.dupe_filter:
                        if self._filter.request_seen(ret):
                            logger.info(f'生产数据：{req.model_dump()}')
                            await self._scheduler.producer(self._channel, queue=self.queue, body=ret)
                    else:
                        logger.info(f'生产数据：{req.model_dump()}')
                        await self._scheduler.producer(self._channel, queue=self.queue, body=ret)

                elif isinstance(req, dict):
                    await self.save_item(req)
        elif isinstance(result, Coroutine):
            await result
        else:
            raise RabbitExpect('回调函数返回类型错误！')

    async def crawl(self):
        session = await self.download.new_session()
        while True:
            try:
                incoming_message: Optional[AbstractIncomingMessage] = await self._scheduler.consumer(self._channel,
                                                                                                     queue=self.queue)
            except QueueEmpty:
                if self.task_manager.all_done():
                    await self.download.exit(session)
                    await self._scheduler.delete_queue(self._channel, self.queue)
                    await self._channel.close()
                    await self._connection.close()
                    break
                else:
                    continue
            except ChannelClosed:
                self._connection, self._channel = self._scheduler.connect()
                logger.warning('mq重新连接!')
                continue
            if incoming_message:
                await self.task_manager.semaphore.acquire()
                self.task_manager.create_task(self.deal_resp(incoming_message, session))
            else:
                print(incoming_message)

    async def consume(self):
        session = await self.download.new_session()
        while True:
            try:
                await self._scheduler.consumer(self._channel, queue=self.queue, callback=self.deal_resp,
                                               prefetch=self._sync,
                                               args=session)
                break
            except ChannelClosed:
                self._connection, self._channel = self._scheduler.connect()
                logger.warning('mq重新连接!')

    async def deal_resp(self, incoming_message: AbstractIncomingMessage, session):
        ret = self.before_request(pickle.loads(incoming_message.body))
        try:
            logger.info(f'消费数据：{ret}')
            response = await self.download.fetch(session, ret)
        except Exception:
            print_exc()
            response = None
        if response and response.status in self.allow_status_code:
            try:
                callback = getattr(self, ret['callback'])
                result = callback(Request(**ret), response)
                if result:
                    await self.routing(result)
            except Exception:
                print_exc()
                for task in asyncio.all_tasks():
                    task.cancel()
        else:
            if ret['retry'] < self.max_retry:
                ret['retry'] += 1
                await self._scheduler.producer(self._channel, queue=self.queue, body=pickle.dumps(ret),
                                               priority=ret['retry'])
            else:
                logger.error(f'请求失败：{ret}')
        await incoming_message.ack()

    async def run(self, mode):

        self._filter = RFPDupeFilter(self.settings.get('REDIS_FILTER_NAME'),
                                     self.settings.get('REDIS_QUEUE_HOST'),
                                     self.settings.get('REDIS_QUEUE_PORT'),
                                     self.settings.get('REDIS_QUEUE_DB'))

        self._scheduler = Scheduler(self.settings.get('RABBIT_USERNAME'),
                                    self.settings.get('RABBIT_PASSWORD'),
                                    self.settings.get('RABBIT_HOST'),
                                    self.settings.get('RABBIT_PORT'),
                                    self.settings.get('RABBIT_VIRTUAL_HOST'))

        self.max_retry = self.settings.get('MAX_RETRY')

        self._connection, self._channel = self._scheduler.connect()

        if mode == 'auto':
            await self.start_spider()
            await self.crawl()
        elif mode == 'm':
            await self.start_spider()
        elif mode == 'w':
            await self.consume()
        else:
            raise RabbitExpect('执行模式错误！')
