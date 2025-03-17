import os
import re
import sys
import time
import asyncio
from typing import Type, List
from croniter import croniter
from datetime import datetime
from RabbitSpider.spider import Spider
from RabbitSpider.core.engine import Engine
from RabbitSpider.utils.control import TaskManager, SettingManager
from importlib.util import spec_from_file_location, module_from_spec


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
    async with Engine(mode, task_count) as engine:
        await engine.start(spider_cls())


async def batch_go(spiders: List[Type[Spider]], task_pool: int = 10):
    settings = SettingManager()
    settings.set('MODE', 'auto')
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


def runner(directory, task_pool, cron_expression):
    cls_list = []
    next_time = None
    sys.path.append(os.path.abspath('.'))
    sys.path.append(os.path.abspath('..'))
    for filename in os.listdir(os.path.join('spiders', directory)):
        if filename.endswith('.py'):
            with open(os.path.join('spiders', directory, filename), 'r', encoding='utf-8') as file:
                classname = re.findall(r'class\s.*?(\w+)\s*?\(\w+\)', file.read())[0]
                spec = spec_from_file_location(classname, os.path.join('spiders', directory, filename))
                module = module_from_spec(spec)
                spec.loader.exec_module(module)
                cls_list.append(getattr(module, classname))

    if croniter.is_valid(cron_expression):
        cron = croniter(cron_expression, datetime.now()).all_next(datetime)
        while True:
            now_time = datetime.strptime(datetime.now().strftime('%Y-%m-%d %H:%M'), '%Y-%m-%d %H:%M')
            if now_time == next_time:
                asyncio.run(batch_go(cls_list, task_pool))
            if not next_time or next_time <= now_time:
                next_time = next(cron)
                print(f'下次运行时间：{next_time}')
            else:
                time.sleep(5)
    else:
        asyncio.run(batch_go(cls_list, task_pool))
