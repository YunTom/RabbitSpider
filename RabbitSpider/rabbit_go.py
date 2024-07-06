import sys
import asyncio
import requests
import socket
from datetime import datetime, timedelta
from traceback import print_exc
from signal import signal, SIGINT, SIGTERM


async def main(spider, mode, task_count, timer):
    try:
        rabbit = spider(task_count)
    except Exception:
        print_exc()
        raise

    def signal_handler(sig, frame):
        requests.post('http://127.0.0.1:8000/post/task',
                      json={'name': rabbit.name, 'status': 0,
                            'stop_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')})

    signal(SIGINT, signal_handler)
    signal(SIGTERM, signal_handler)
    try:
        requests.post('http://127.0.0.1:8000/post/task',
                      json={'name': rabbit.name, 'ip_address': f'{socket.gethostbyname(socket.gethostname())}',
                            'sync': task_count, 'status': 1})
        await rabbit.run(mode)
        if timer:
            requests.post('http://127.0.0.1:8000/post/task',
                          json={'name': rabbit.name,
                                'sleep': timer,
                                'next_time': (datetime.now() + timedelta(minutes=timer)).strftime('%Y-%m-%d %H:%M:%S')})
        elif mode == 'auto':
            requests.post('http://127.0.0.1:8000/delete/queue', json={'name': rabbit.name})
    except Exception:
        print_exc()


async def go(spider, mode: str = 'auto', task_count: int = 1, timer=0):
    for i in sys.argv[1:]:
        key, value = i.split('=')
        if key == 'mode':
            mode = value
        if key == 'task_count':
            task_count = value
    while timer:
        await main(spider, mode=mode, task_count=task_count, timer=timer)
        await asyncio.sleep(timer * 60)
    else:
        await main(spider, mode=mode, task_count=task_count, timer=timer)
