import sys
import os
import asyncio
import requests
import socket
from datetime import datetime
from traceback import print_exc
from signal import signal, SIGINT, SIGTERM


def main(spider, mode, task_count):
    try:
        rabbit = spider(task_count)
    except Exception:
        print_exc()
        raise

    def signal_handler(sig, frame):
        requests.post('http://127.0.0.1:8000/post/task',
                      json={'status': 0, 'stop_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'pid': os.getpid()})

    signal(SIGINT, signal_handler)
    signal(SIGTERM, signal_handler)
    try:
        requests.post('http://127.0.0.1:8000/post/task',
                      json={'name': rabbit.name, 'ip_address': f'{socket.gethostbyname(socket.gethostname())}',
                            'task_count': task_count, 'status': 1, 'pid': os.getpid(), 'mode': mode,
                            'create_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'dir': os.path.abspath(os.path.dirname(sys.argv[0]))})
        loop = asyncio.get_event_loop()
        loop.run_until_complete(rabbit.run(mode))

        requests.post('http://127.0.0.1:8000/post/task',
                      json={'pid': os.getpid(), 'name': rabbit.name, 'status': 2})

    except Exception:
        print_exc()


def go(spider, mode: str = 'auto', task_count: int = 1):
    for i in sys.argv[1:]:
        key, value = i.split('=')
        if key == 'mode':
            mode = value
        if key == 'task_count':
            task_count = int(value)
    main(spider, mode=mode, task_count=task_count)
