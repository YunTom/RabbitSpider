import asyncio
import os
import pickle
import sys
from collections.abc import AsyncGenerator, Coroutine
from traceback import print_exc
from typing import Optional
from aio_pika.abc import AbstractIncomingMessage
from RabbitSpider.http.request import Request
from RabbitSpider.http.response import Response
from RabbitSpider.utils.control import TaskManager
from RabbitSpider.utils.control import SettingManager
from RabbitSpider.utils.control import PipelineManager
from RabbitSpider.utils.dupefilter import RFPDupeFilter
from RabbitSpider.utils.expections import RabbitExpect
from RabbitSpider.utils.log import Logger
from RabbitSpider.core.scheduler import Scheduler
from RabbitSpider.core.download import CurlDownload
from curl_cffi import CurlHttpVersion
from aio_pika.exceptions import QueueEmpty


class Engine(object):
    name = os.path.basename(sys.argv[0])
    allow_status_code: list = [200]
    max_retry: int = 5
    http_version = CurlHttpVersion.V1_0
    tls = "chrome120"

    def __init__(self, sync):
        self.session = None
        self._future = None
        self._connection = None
        self._channel = None
        self._sync = sync
        self.settings = SettingManager()
        self._filter = RFPDupeFilter(self.name,
                                     self.settings.get('REDIS_QUEUE_HOST'),
                                     self.settings.get('REDIS_QUEUE_PORT'),
                                     self.settings.get('REDIS_QUEUE_DB'))
        self._scheduler = Scheduler(self.settings.get('RABBIT_USERNAME'),
                                    self.settings.get('RABBIT_PASSWORD'),
                                    self.settings.get('RABBIT_HOST'),
                                    self.settings.get('RABBIT_PORT'),
                                    self.settings.get('RABBIT_VIRTUAL_HOST'))
        self.logger = Logger(self.settings, self.name).logger
        self._task_manager = TaskManager(self._sync)
        self._download = CurlDownload(http_version=self.http_version, impersonate=self.tls)
        self.pipelines = PipelineManager.create_instance(self)

    async def start_spider(self):
        self._connection, self._channel = await self._scheduler.connect()
        await self.pipelines.methods['open_spider'](self)
        await self._scheduler.create_queue(self._channel, self.name)
        self.session = await self._download.new_session()
        await self.routing(self.start_requests())

    async def start_requests(self):
        """初始请求"""
        pass

    async def parse(self, request: Request, response: Response):
        """默认回调"""
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
                            self.logger.info(f'生产数据：{req.model_dump()}')
                            await self._scheduler.producer(self._channel, queue=self.name, body=ret)
                    else:
                        self.logger.info(f'生产数据：{req.model_dump()}')
                        await self._scheduler.producer(self._channel, queue=self.name, body=ret)

                elif isinstance(req, dict):
                    await self.pipelines.methods['process_item'](req,self)
        elif isinstance(result, Coroutine):
            await result
        else:
            raise RabbitExpect('回调函数返回类型错误！')

    async def crawl(self):
        while True:
            try:
                incoming_message: Optional[AbstractIncomingMessage] = await self._scheduler.consumer(self._channel,
                                                                                                     queue=self.name)
            except QueueEmpty:
                if self._task_manager.all_done():
                    await self._download.exit(self.session)
                    await self._scheduler.delete_queue(self._channel, self.name)
                    await self._channel.close()
                    await self._connection.close()
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
        ret = self.before_request(pickle.loads(incoming_message.body))
        self.logger.info(f'消费数据：{ret}')
        try:
            response = await self._download.fetch(self.session, ret)
        except Exception as e:
            self.logger.error(f'请求失败：{e}')
            print_exc()
            response = None
        if response and response.status in self.allow_status_code:
            try:
                callback = getattr(self, ret['callback'])
                result = callback(Request(**ret), response)
                if result:
                    await self.routing(result)
            except Exception as e:
                self.logger.error(f'请求失败：{e}')
                print_exc()
                for task in asyncio.all_tasks():
                    task.cancel()
        else:
            if ret['retry'] < self.max_retry:
                ret['retry'] += 1
                await self._scheduler.producer(self._channel, queue=self.name, body=pickle.dumps(ret),
                                               priority=ret['retry'])
            else:
                self.logger.error(f'请求失败：{ret}')
        try:
            await self._channel.declare_queue(name=self.name, passive=True)
            await incoming_message.ack()
        except Exception:
            self._future.set_result('done') if self._future else None
            self.logger.info(f'队列{self.name}已删除！')

    async def run(self, mode):
        if mode == 'auto':
            await self.start_spider()
            await self.crawl()
        elif mode == 'm':
            await self.start_spider()
        elif mode == 'w':
            await self.consume()
        else:
            raise RabbitExpect('执行模式错误！')
        await self.pipelines.methods['close_spider'](self)
