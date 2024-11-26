import asyncio
import sys
from typing import Type, List
from traceback import print_exc
from asyncio.exceptions import CancelledError
from RabbitSpider.core.download import CurlDownload
from RabbitSpider.core.scheduler import Scheduler
from RabbitSpider.core.engine import Engine
from RabbitSpider.spider import Spider
from RabbitSpider.utils import event
from RabbitSpider.utils.log import Logger
from RabbitSpider.utils.subscriber import Subscriber
from RabbitSpider.utils.control import SettingManager, MiddlewareManager
from RabbitSpider.utils.control import TaskManager, PipelineManager, FilterManager


class Crawler(object):
    def __init__(self, spider: Type[Spider], mode: str, task_count: int):
        self.mode = mode
        self.task_count = task_count
        self.settings = SettingManager()
        self.subscriber = Subscriber()
        self.settings.update(spider.custom_settings)
        self.logger = Logger(self.settings, spider.name)
        self.download = CurlDownload(self.settings)
        self.session = self.download.session
        self.spider = spider(self)
        self.scheduler = Scheduler(self.settings)
        self.filter = FilterManager(self)
        self.pipeline = PipelineManager(self)
        self.task_manager = TaskManager(self.task_count)
        self.middlewares = MiddlewareManager(self)
        loop = asyncio.get_running_loop()
        loop.set_exception_handler(self.custom_exception_handler)

    def custom_exception_handler(self, loop, context):
        self.logger.error(f"Exception in loop {loop} : {context['future'].exception()}")
        try:
            for task in asyncio.all_tasks():
                task.cancel()
        except RuntimeError:
            pass

    async def process(self):
        async with Engine(self) as engine:
            self.logger.info(f'任务{self.spider.name}启动')
            await self.subscriber.notify(event.spider_opened, self.spider)
            try:
                await engine.start()
            except CancelledError as exc:
                self.logger.error(f'任务{self.spider.name}异常')
                await self.subscriber.notify(event.spider_error, self.spider, exc)
            except Exception as exc:
                self.logger.error(f'任务{self.spider.name}异常')
                await self.subscriber.notify(event.spider_error, self.spider, exc)
                print_exc()
            else:
                await self.subscriber.notify(event.spider_closed, self.spider)
                self.logger.info(f'任务{self.spider.name}结束')


async def main(spider, mode, task_count):
    try:
        crawler = Crawler(spider, mode, task_count)
        await crawler.process()
    except Exception:
        print_exc()
        raise


async def go(spider: Type[Spider], mode: str = 'auto', task_count: int = 1):
    for i in sys.argv[1:]:
        key, value = i.split('=')
        if key == 'mode':
            mode = value
        if key == 'task_count':
            task_count = int(value)
    await main(spider, mode=mode, task_count=task_count)


async def batch_go(spiders: List[Type[Spider]], task_pool: int = 10):
    task_manager = TaskManager(task_pool)
    for spider in spiders:
        await task_manager.semaphore.acquire()
        task_manager.create_task(main(spider, mode='auto', task_count=1))
    while True:
        if task_manager.all_done():
            break
        else:
            await asyncio.sleep(1)
