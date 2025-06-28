import sys
import asyncio
from typing import Type, List
from RabbitSpider.spider import Spider
from RabbitSpider.core.engine import Engine
from RabbitSpider.utils.control import TaskManager, SettingManager


async def go(spider_cls: Type[Spider], mode: str = 'auto', task_count: int = 1):
    settings = SettingManager()
    for i in sys.argv[1:]:
        key, value = i.split('=')
        if key == 'mode':
            mode = value
        if key == 'task_count':
            task_count = int(value)
    settings.set('MODE', mode)
    settings.set('TASK_COUNT', task_count)
    settings.set('CHANNEL_SIZE', task_count * 3)
    async with Engine(settings) as engine:
        await engine.start(spider_cls())


async def batch_go(spiders: List[Type[Spider]], task_count: int = 10):
    settings = SettingManager()
    settings.set('MODE', 'auto')
    settings.set('TASK_COUNT', task_count)
    settings.set('CHANNEL_SIZE', task_count * 3)
    task_group: TaskManager = TaskManager(task_count)
    async with Engine(settings) as engine:
        for spider_cls in spiders:
            await task_group.semaphore.acquire()
            task_group.create_task(engine.start(spider_cls()))
        while True:
            if task_group.all_done():
                break
            else:
                await asyncio.sleep(1)
