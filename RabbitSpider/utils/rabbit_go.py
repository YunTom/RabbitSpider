import sys
import asyncio
import time
import requests
import socket
from datetime import datetime, timedelta
from traceback import print_exc
from signal import signal, SIGINT, SIGTERM
from asyncio import WindowsSelectorEventLoopPolicy


def main(spider, mode, sync, timer):
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(WindowsSelectorEventLoopPolicy())
    loop = asyncio.get_event_loop()
    try:
        rabbit = spider(sync)
    except Exception:
        print_exc()
        raise

    # def signal_handler(sig, frame):
    #     requests.post('http://127.0.0.1:8000/post/task',
    #                   json={'name': rabbit.name, 'status': 0,
    #                         'stop_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')})
    #
    # signal(SIGINT, signal_handler)
    # signal(SIGTERM, signal_handler)
    try:
        # requests.post('http://127.0.0.1:8000/post/task',
        #               json={'name': rabbit.name, 'ip_address': f'{socket.gethostbyname(socket.gethostname())}',
        #                     'sync': sync, 'status': 1})
        loop.run_until_complete(rabbit.run(mode))
        # if timer:
        #     requests.post('http://127.0.0.1:8000/post/task',
        #                   json={'name': rabbit.name,
        #                         'sleep': timer,
        #                         'next_time': (datetime.now() + timedelta(minutes=timer)).strftime('%Y-%m-%d %H:%M:%S')})
        # elif mode == 'auto':
        #     requests.post('http://127.0.0.1:8000/delete/queue', json={'name': rabbit.name})
    except Exception:
        print_exc()


def go(spider, mode: str = 'auto', sync: int = 1, timer: int = 0):
    for i in sys.argv[1:]:
        key, value = i.split('=')
        if key == 'mode':
            mode = value
        if key == 'sync':
            sync = value
    while timer:
        main(spider, mode=mode, sync=sync, timer=timer)
        time.sleep(timer * 60)
    else:
        main(spider, mode=mode, sync=sync, timer=timer)
