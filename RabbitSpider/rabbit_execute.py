import asyncio
import sys
import os
import requests
import socket
from datetime import datetime
from typing import Type, List
from traceback import print_exc
from signal import signal, SIGINT, SIGTERM
from RabbitSpider.utils.control import TaskManager

logo = r"""
    ____             __      __      _    __    _____             _        __              
   / __ \  ____ _   / /_    / /_    (_)  / /_  / ___/    ____    (_)  ____/ /  ___    _____
  / /_/ / / __ `/  / __ \  / __ \  / /  / __/  \__ \    / __ \  / /  / __  /  / _ \  / ___/
 / _, _/ / /_/ /  / /_/ / / /_/ / / /  / /_   ___/ /   / /_/ / / /  / /_/ /  /  __/ / /    
/_/ |_|  \__,_/  /_.___/ /_.___/ /_/   \__/  /____/   / .___/ /_/   \__,_/   \___/ /_/     
                                                     /_/                                   
"""


async def main(spider, mode, task_count):
    try:
        rabbit = spider(task_count)
        sys.stdout.write(f'\033[0;35;1m{logo}\033[0m')
    except Exception:
        print_exc()
        raise

    # def signal_handler(sig, frame):
    #     requests.post('http://60.204.154.131:8000/post/task',
    #                   json={'status': 0, 'stop_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'pid': os.getpid()})
    #
    # signal(SIGINT, signal_handler)
    # signal(SIGTERM, signal_handler)
    try:
        # requests.post('http://60.204.154.131:8000/post/task',
        #               json={'name': rabbit.name, 'ip_address': f'{socket.gethostbyname(socket.gethostname())}',
        #                     'task_count': task_count, 'status': 1, 'pid': os.getpid(), 'mode': mode,
        #                     'create_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        #                     'dir': os.path.abspath(os.path.dirname(sys.argv[0]))})
        await rabbit.run(mode)

        # requests.post('http://60.204.154.131:8000/post/task',
        #               json={'pid': os.getpid(), 'name': rabbit.name, 'status': 2, 'mode': mode})

    except Exception:
        print_exc()


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
