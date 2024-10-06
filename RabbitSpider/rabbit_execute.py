import asyncio
import sys
from typing import Type, List
from traceback import print_exc
from RabbitSpider.core.download import CurlDownload
from RabbitSpider.core.scheduler import Scheduler
from RabbitSpider.core.engine import Engine
from RabbitSpider.spider import Spider
from RabbitSpider.utils import event
from RabbitSpider.utils.subscriber import Subscriber
from RabbitSpider.utils.control import SettingManager
from asyncio.exceptions import CancelledError
from RabbitSpider.utils.control import TaskManager, PipelineManager, FilterManager


class Crawler(object):
    def __init__(self, spider: Type[Spider], mode: str, task_count: int):
        self.mode = mode
        self.task_count = task_count
        self.settings = SettingManager()
        self.subscriber = Subscriber.create_instance()
        self.spider = spider(self)
        self.scheduler = Scheduler(self.settings)
        self.filter = FilterManager(self)
        self.pipeline = PipelineManager.create_instance(self)
        self.task_manager = TaskManager(self.task_count)
        self.download = CurlDownload.create_instance(self)

    async def process(self):
        self.spider.logger.info(f'任务{self.spider.name}启动')
        self.subscriber.notify(event.spider_opened, self.spider)
        try:
            async with Engine(self) as engine:
                await engine.start()
        except CancelledError as exc:
            self.spider.logger.error(f'任务{self.spider.name}中止')
            self.subscriber.notify(event.spider_error, self.spider, exc)
        except Exception as exc:
            self.spider.logger.error(f'任务{self.spider.name}中止')
            self.subscriber.notify(event.spider_error, self.spider, exc)
        else:
            self.subscriber.notify(event.spider_closed, self.spider)
            self.spider.logger.info(f'任务{self.spider.name}结束')


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
        task_manager.create_task(go(spider, mode='auto', task_count=1))
    while True:
        if task_manager.all_done():
            break
        else:
            await asyncio.sleep(1)
