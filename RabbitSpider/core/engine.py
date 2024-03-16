import asyncio
import os
import sys
import pickle
from traceback import print_exc
from datetime import datetime
from collections.abc import AsyncGenerator, Coroutine
from abc import ABC, abstractmethod
from typing import Optional
from aio_pika.abc import AbstractIncomingMessage
from aio_pika.exceptions import QueueEmpty
from RabbitSpider import redis_filter
from RabbitSpider import download
from RabbitSpider import scheduler
from RabbitSpider import max_retry
from RabbitSpider.utils.control import TaskManager
from RabbitSpider.utils.expections import RabbitExpect
from RabbitSpider.http.request import Request
from loguru import logger

logger.add(f'./spider_log/{datetime.strftime(datetime.now(), "%Y-%m-%d")}.log', rotation="1 day")


class Engine(ABC):
    def __init__(self, sync):
        self.session = None
        self.consuming = False
        self.queue = os.path.basename(sys.argv[0])
        self.allow_status_code: list = [200]
        self.max_retry: int = max_retry
        self.filter = redis_filter
        self.download = download
        self.scheduler = scheduler
        self.task_manager = TaskManager(sync)

    async def start_spider(self):
        await self.scheduler.create_queue(self.queue)
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

    async def close_spider(self):
        """任务结束"""
        pass

    async def routing(self, result):
        if isinstance(result, AsyncGenerator):
            async for req in result:
                if isinstance(req, Request):
                    ret = pickle.dumps(req.model_dump())
                    if req.dupe_filter:
                        if self.filter.request_seen(ret):
                            logger.info(f'生产数据{req.model_dump()}')
                            await self.scheduler.producer(queue=self.queue, body=ret)
                    else:
                        logger.info(f'生产数据{req.model_dump()}')
                        await self.scheduler.producer(queue=self.queue, body=ret)

                elif isinstance(req, dict):
                    await self.save_item(req)
        elif isinstance(result, Coroutine):
            await result
        else:
            raise RabbitExpect('回调函数返回类型错误！')

    async def crawl(self):
        self.session = await self.download.new_session()
        while True:
            try:
                incoming_message: Optional[AbstractIncomingMessage] = await self.scheduler.consumer(queue=self.queue)
            except QueueEmpty:
                if self.consuming:
                    logger.info('没有任务数据！')
                    await asyncio.sleep(3)
                    continue
                elif self.task_manager.all_done():
                    await self.download.exit(self.session)
                    await self.scheduler.delete_queue(self.queue)
                    break
                else:
                    continue
            if incoming_message:
                await self.task_manager.semaphore.acquire()
                self.task_manager.create_task(self.deal_resp(incoming_message))
            else:
                print(incoming_message)

    async def deal_resp(self, incoming_message: AbstractIncomingMessage):
        ret = pickle.loads(incoming_message.body)
        try:
            logger.info(f'消费数据{ret}')
            response = await self.download.fetch(self.session, ret)
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
                await self.scheduler.producer(queue=self.queue, body=pickle.dumps(ret), priority=ret['retry'])
            else:
                logger.error(f'请求失败{ret}')
        await incoming_message.ack()

    async def run(self):
        await self.start_spider()
        await self.crawl()
        await self.close_spider()
