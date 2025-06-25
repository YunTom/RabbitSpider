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


def runner(spider_dir, task_pool, cron_expr):
    spider_classes = []
    loop = asyncio.get_event_loop()
    spider_path = os.path.join('spiders', spider_dir)
    sys.path.extend([os.path.abspath('.'), os.path.abspath('..')])

    for script_name in os.listdir(spider_path):
        if script_name.endswith('.py') and not script_name.startswith('__'):
            script_path = os.path.join(spider_path, script_name)
            with open(script_path, 'r', encoding='utf-8') as file:
                class_name = re.findall(r'class\s+(\w+)\s*\(\w+\)', file.read())[0]
                spec = spec_from_file_location(class_name, script_path)
                module = module_from_spec(spec)
                spec.loader.exec_module(module)
                spider_classes.append(getattr(module, class_name))

    if croniter.is_valid(cron_expr):
        cron_schedule = croniter(cron_expr, datetime.now())
        next_run_time = cron_schedule.get_next(datetime)
        print(f'下次运行时间：{next_run_time}')
        while True:
            now_time = datetime.now().replace(second=0, microsecond=0)
            if now_time == next_run_time:
                loop.run_until_complete(batch_go(spider_classes, task_pool))
            if next_run_time <= now_time:
                next_run_time = cron_schedule.get_next(datetime)
                print(f'下次运行时间：{next_run_time}')
            else:
                time.sleep(5)
    else:
        loop.run_until_complete(batch_go(spider_classes, task_pool))
        loop.close()
