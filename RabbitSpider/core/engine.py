import asyncio
import os
import sys
import pickle
from collections.abc import AsyncGenerator, Coroutine
from traceback import print_exc
from typing import Optional
from aio_pika.abc import AbstractIncomingMessage
from RabbitSpider.http.request import Request
from RabbitSpider.http.response import Response
from RabbitSpider.utils.control import TaskManager
from RabbitSpider.utils.control import SettingManager
from RabbitSpider.utils.control import PipelineManager
from RabbitSpider.utils.control import MiddlewareManager
from RabbitSpider.utils.dupefilter import RFPDupeFilter
from RabbitSpider.utils.expections import RabbitExpect
from RabbitSpider.utils.log import Logger
from RabbitSpider.items import Item
from RabbitSpider.core.scheduler import Scheduler
from curl_cffi import CurlHttpVersion
from aio_pika.exceptions import QueueEmpty


class Engine(object):
    name = os.path.basename(sys.argv[0])
    http_version = CurlHttpVersion.V1_0
    impersonate = "chrome120"

    def __init__(self, sync):
        self.session = None
        self._future = None
        self._connection = None
        self._channel = None
        self._sync = sync
        self.settings = SettingManager()
        self._scheduler = Scheduler(self.settings.get('RABBIT_USERNAME'),
                                    self.settings.get('RABBIT_PASSWORD'),
                                    self.settings.get('RABBIT_HOST'),
                                    self.settings.get('RABBIT_PORT'),
                                    self.settings.get('RABBIT_VIRTUAL_HOST'))
        self._filter = RFPDupeFilter(self.name,
                                     self.settings.get('REDIS_QUEUE_HOST'),
                                     self.settings.get('REDIS_QUEUE_PORT'),
                                     self.settings.get('REDIS_QUEUE_DB'))
        self.logger = Logger(self.settings, self.name).logger
        self._task_manager = TaskManager(self._sync)
        self.middlewares = MiddlewareManager.create_instance(self.http_version, self.impersonate, self)
        self.pipelines = PipelineManager.create_instance(self)

    async def start_requests(self):
        """初始请求"""
        pass

    async def parse(self, request: Request, response: Response):
        """默认回调"""
        pass

    async def routing(self, result):
        async def rule(res):
            if isinstance(res, Request):
                ret = pickle.dumps(res.model_dump())
                if res.dupe_filter:
                    if self._filter.request_seen(ret):
                        self.logger.info(f'生产数据：{res.model_dump()}')
                        await self._scheduler.producer(self._channel, queue=self.name, body=res.model_dump())
                else:
                    self.logger.info(f'生产数据：{res.model_dump()}')
                    await self._scheduler.producer(self._channel, queue=self.name, body=res.model_dump())
            elif isinstance(res, Item):
                await self.pipelines.process_item(res)

        if isinstance(result, AsyncGenerator):
            async for r in result:
                await rule(r)
        elif isinstance(result, Coroutine):
            r = await result
            await rule(r)
        elif isinstance(result, Request):
            await rule(result)
        else:
            raise RabbitExpect('回调函数返回类型错误！')

    async def produce(self):
        await self._scheduler.create_queue(self._channel, self.name)
        await self.routing(self.start_requests())

    async def crawl(self):
        while True:
            try:
                incoming_message: Optional[AbstractIncomingMessage] = await self._scheduler.consumer(self._channel,
                                                                                                     queue=self.name)
            except QueueEmpty:
                if self._task_manager.all_done():
                    await self._scheduler.delete_queue(self._channel, self.name)
                    break
                else:
                    continue
            except Exception:
                break
            if incoming_message:
                await self._task_manager.semaphore.acquire()
                self._task_manager.create_task(self.deal_resp(incoming_message))
            else:
                print(incoming_message)

    async def consume(self):
        await self._scheduler.consumer(self._channel, queue=self.name, callback=self.deal_resp,
                                       prefetch=self._sync)
        self._future = asyncio.Future()
        await self._future

    async def deal_resp(self, incoming_message):
        ret = pickle.loads(incoming_message.body)
        self.logger.info(f'消费数据：{ret}')
        response = await self.middlewares.downloader(Request(**ret))
        if response:
            try:
                callback = getattr(self, ret['callback'])
                result = callback(Request(**ret), response)
                if result:
                    await self.routing(result)
            except Exception as e:
                self.logger.error(f'解析失败：{e}')
                print_exc()
                for task in asyncio.all_tasks():
                    task.cancel()
        try:
            await self._channel.declare_queue(name=self.name, passive=True)
        except Exception:
            self._future.set_result('done') if self._future else None
            self.logger.info(f'队列{self.name}已删除！')
        else:
            await incoming_message.ack()

    async def run(self, mode):
        self.logger.info(f'{self.name}任务开始')
        self._connection, self._channel = await self._scheduler.connect()
        self.session = await self.middlewares.download.new_session()
        await self.pipelines.open_spider()
        if mode == 'auto':
            await self.produce()
            await self.crawl()
        elif mode == 'm':
            await self.produce()
        elif mode == 'w':
            await self.consume()
        else:
            raise RabbitExpect('执行模式错误！')
        await self.pipelines.close_spider()
        await self._channel.close()
        await self._connection.close()
        await self.middlewares.download.exit(self.session)
        self.logger.info(f'{self.name}任务完成')
