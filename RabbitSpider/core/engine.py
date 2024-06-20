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
from RabbitSpider.utils.exceptions import RabbitExpect
from RabbitSpider.utils.log import Logger
from RabbitSpider.items.item import Item
from RabbitSpider.core.scheduler import Scheduler
from aio_pika.exceptions import QueueEmpty


class Engine(object):
    name = os.path.basename(sys.argv[0])
    custom_settings = {}

    def __init__(self, sync):
        self.session = None
        self.__future = None
        self.__connection = None
        self.__channel = None
        self.__sync = sync
        self.settings = SettingManager(self.custom_settings)
        self.logger = Logger(self.settings, self.name).logger
        self.__task_manager = TaskManager(self.__sync)
        self.__middlewares = MiddlewareManager.create_instance(self)
        self.__pipelines = PipelineManager.create_instance(self)
        self.__scheduler = Scheduler(self.settings.get('RABBIT_USERNAME'),
                                     self.settings.get('RABBIT_PASSWORD'),
                                     self.settings.get('RABBIT_HOST'),
                                     self.settings.get('RABBIT_PORT'),
                                     self.settings.get('RABBIT_VIRTUAL_HOST'))
        self.__filter = RFPDupeFilter(self.name,
                                      self.settings.get('REDIS_HOST'),
                                      self.settings.get('REDIS_PORT'),
                                      self.settings.get('REDIS_DB'))

    async def start_requests(self):
        """初始请求"""
        pass

    async def parse(self, request: Request, response: Response):
        """默认回调"""
        pass

    async def routing(self, result):
        async def rule(res):
            if isinstance(res, Request):
                if res.dupe_filter:
                    if self.__filter.request_seen(res.model_dump()):
                        self.logger.info(f'生产数据：{res.model_dump()}')
                        await self.__scheduler.producer(self.__channel, queue=self.name, body=res.model_dump())
                else:
                    self.logger.info(f'生产数据：{res.model_dump()}')
                    await self.__scheduler.producer(self.__channel, queue=self.name, body=res.model_dump())
            elif isinstance(res, Item):
                await self.__pipelines.process_item(res)

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
        await self.__scheduler.create_queue(self.__channel, self.name)
        await self.routing(self.start_requests())

    async def crawl(self):
        while True:
            try:
                incoming_message: Optional[AbstractIncomingMessage] = await self.__scheduler.consumer(self.__channel,
                                                                                                      queue=self.name)
            except QueueEmpty:
                if self.__task_manager.all_done():
                    await self.__scheduler.delete_queue(self.__channel, self.name)
                    break
                else:
                    continue
            except Exception:
                break
            if incoming_message:
                await self.__task_manager.semaphore.acquire()
                self.__task_manager.create_task(self.deal_resp(incoming_message))
            else:
                print(incoming_message)

    async def consume(self):
        await self.__scheduler.consumer(self.__channel, queue=self.name, callback=self.deal_resp,
                                        prefetch=self.__sync)
        self.__future = asyncio.Future()
        await self.__future

    async def deal_resp(self, incoming_message):
        ret = pickle.loads(incoming_message.body)
        self.logger.info(f'消费数据：{ret}')
        response = await self.__middlewares.downloader(Request(**ret))
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
            await self.__channel.declare_queue(name=self.name, passive=True)
        except Exception:
            self.__future.set_result('done') if self.__future else None
            self.logger.info(f'队列{self.name}已删除！')
        else:
            await incoming_message.ack()

    async def run(self, mode):
        self.logger.info(f'{self.name}任务开始')
        self.__connection, self.__channel = await self.__scheduler.connect()
        self.session = await self.__middlewares.download.new_session()
        await self.__pipelines.open_spider()
        if mode == 'auto':
            await self.produce()
            await self.crawl()
        elif mode == 'm':
            await self.produce()
        elif mode == 'w':
            await self.consume()
        else:
            raise RabbitExpect('执行模式错误！')
        await self.__pipelines.close_spider()
        await self.__channel.close()
        await self.__connection.close()
        await self.__middlewares.download.exit(self.session)
        self.logger.info(f'{self.name}任务完成')
