import sys
import asyncio
from typing import Type, List
from RabbitSpider.spider import Spider
from RabbitSpider.core.engine import Engine
from RabbitSpider.utils.control import TaskManager


async def go(spider_cls: Type[Spider], mode: str = 'auto', task_count: int = 1):
    for i in sys.argv[1:]:
        key, value = i.split('=')
        if key == 'mode':
            mode = value
        if key == 'task_count':
            task_count = int(value)
    async with Engine(mode, task_count) as engine:
        await engine.start(spider_cls())


async def batch_go(spiders: List[Type[Spider]], task_pool: int = 10):
    task_group: TaskManager = TaskManager(task_pool)
    async with Engine(mode='auto', task_count=task_pool) as engine:
        for spider_cls in spiders:
            await task_group.semaphore.acquire()
            task_group.create_task(engine.start(spider_cls()))
        while True:
            if task_group.all_done():
                break
            else:
                await asyncio.sleep(1)
