import sys
import asyncio
import time

import requests
from datetime import datetime, timedelta
from RabbitSpider import setting
from traceback import print_exc
from signal import signal, SIGINT, SIGTERM
from RabbitSpider.utils.expections import RabbitExpect


def main(spider, mode, sync, timer):
    loop = asyncio.get_event_loop()
    try:
        rabbit = spider(sync)
    except Exception:
        print_exc()
        raise

    def signal_handler(sig, frame):
        requests.post('http://127.0.0.1:8000/post/task',
                      json={'name': rabbit.queue, 'status': 0,
                            'stop_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')})

    signal(SIGINT, signal_handler)
    signal(SIGTERM, signal_handler)
    try:
        requests.post('http://127.0.0.1:8000/post/task',
                      json={'name': rabbit.queue, 'ip_address': '127.0.0.1', 'sync': sync, 'status': 1})
        if mode == 'auto':
            loop.run_until_complete(rabbit.run())
        elif mode == 'm':
            loop.run_until_complete(rabbit.start_spider())
        elif mode == 'w':
            loop.run_until_complete(rabbit.crawl())
        else:
            raise RabbitExpect('执行模式错误！')
        requests.post('http://127.0.0.1:8000/post/task',
                      json={'name': rabbit.queue,
                            'next_time': (datetime.now() + timedelta(minutes=timer)).strftime('%Y-%m-%d %H:%M:%S')})
    except Exception:
        print_exc()


def go(spider: object, mode: str = 'auto', sync: int = setting.get('ASYNC_CONT'), timer: int = 0):
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
