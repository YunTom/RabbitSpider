import asyncio
import sys
from typing import Type, List
from traceback import print_exc
from RabbitSpider.utils.control import TaskManager


async def main(spider, mode, task_count):
    try:
        rabbit = spider(task_count)
        await rabbit.run(mode)
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
