import asyncio
import sys
from typing import Type, List
from traceback import print_exc
from RabbitSpider.utils.control import TaskManager
from RabbitSpider.core.engine import Engine
from RabbitSpider.spider import Spider
from RabbitSpider.utils import event
from RabbitSpider.utils.subscriber import Subscriber
from RabbitSpider.utils.control import SettingManager
from asyncio.exceptions import CancelledError


class Crawler(object):
    def __init__(self, spider: Type[Spider], mode: str, task_count: int):
        self.settings = SettingManager()
        self.spider = spider()
        self.mode = mode
        self.task_count = task_count
        self.spider.update_settings(self.settings)
        self.subscriber = Subscriber.create_instance()
        self.engine = Engine(self)

    async def process(self):
        self.spider.bind_event(self)
        self.subscriber.notify(event.spider_opened, self.spider)
        try:
            await self.engine.start()
        except CancelledError:
            self.subscriber.notify(event.spider_error, self.spider)
        except Exception:
            self.subscriber.notify(event.spider_error, self.spider)
        else:
            self.subscriber.notify(event.spider_closed, self.spider)


async def main(spider, mode, task_count):
    try:
        crawler = Crawler(spider, mode, task_count)
        await crawler.process()
    except Exception:
        print_exc()
        raise


async def go(spider: Type, mode: str = 'auto', task_count: int = 1):
    for i in sys.argv[1:]:
        key, value = i.split('=')
        if key == 'mode':
            mode = value
        if key == 'task_count':
            task_count = int(value)
    await main(spider, mode=mode, task_count=task_count)


async def batch_go(spiders: List[Type], mode: str = 'auto', task_pool: int = 10):
    task_manager = TaskManager(task_pool)
    for spider in spiders:
        await task_manager.semaphore.acquire()
        task_manager.create_task(go(spider, mode=mode, task_count=1))
    while True:
        if task_manager.all_done():
            break
        else:
            await asyncio.sleep(1)
