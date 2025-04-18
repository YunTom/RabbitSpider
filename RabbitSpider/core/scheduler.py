import pickle
from typing import Callable, Optional
from asyncio.exceptions import TimeoutError
from RabbitSpider.exceptions import RabbitExpect
from aio_pika import connect_robust, Message, pool
from aio_pika.exceptions import AMQPConnectionError, ChannelNotFoundEntity


class Scheduler(object):
    def __init__(self, settings):
        self.connection = None
        self.channel_pool = None
        self.settings = settings
        self.host = settings.get('RABBIT_HOST')
        self.port = settings.get('RABBIT_PORT')
        self.username = settings.get('RABBIT_USERNAME')
        self.password = settings.get('RABBIT_PASSWORD')
        self.channel_size = settings.get('CHANNEL_SIZE')
        self.virtual_host = settings.get('RABBIT_VIRTUAL_HOST')

    @staticmethod
    def retry_exception(func):
        async def inner(self, *args, **kwargs):
            for i in range(self.settings.get('MAX_RETRY')):
                try:
                    result = await func(self, *args, **kwargs)
                except (AMQPConnectionError, TimeoutError):
                    continue
                else:
                    return result
            else:
                raise RabbitExpect('RabbitMq 连接超时！')

        return inner

    @retry_exception
    async def connect(self):
        self.connection = await connect_robust(host=self.host, login=self.username, password=self.password,
                                               virtualhost=self.virtual_host, heartbeat=60, timeout=60)
        self.channel_pool = pool.Pool(self.connection.channel, max_size=self.channel_size)

    @retry_exception
    async def create_queue(self, queue: str):
        async with self.channel_pool.acquire() as channel:
            await channel.declare_queue(name=queue, durable=True, arguments={"x-max-priority": 10}, timeout=60)

    @retry_exception
    async def producer(self, queue: str, body: dict):
        ret = pickle.dumps(body)
        async with self.channel_pool.acquire() as channel:
            await channel.default_exchange.publish(
                Message(body=ret, delivery_mode=2, priority=body['retry_times']), routing_key=queue, timeout=60)

    @retry_exception
    async def consumer(self, spider, callback: Optional[Callable] = None, prefetch: int = 1):
        async with self.channel_pool.acquire() as channel:
            try:
                queue = await channel.declare_queue(name=spider.name, durable=True, passive=True, timeout=60)
            except ChannelNotFoundEntity:
                queue = await channel.declare_queue(name=spider.name, durable=True, arguments={"x-max-priority": 10},
                                                    timeout=60)
            if callback:
                await channel.set_qos(prefetch_count=prefetch)
                await queue.consume(callback=lambda incoming_message: callback(spider, incoming_message))
            else:
                return await queue.get(fail=False, timeout=60)

    @retry_exception
    async def queue_purge(self, queue: str):
        async with self.channel_pool.acquire() as channel:
            queue = await channel.declare_queue(name=queue, durable=True, passive=True, timeout=60)
            await queue.purge()

    @retry_exception
    async def delete_queue(self, queue: str):
        async with self.channel_pool.acquire() as channel:
            await channel.queue_delete(queue)

    @retry_exception
    async def get_message_count(self, queue: str):
        async with self.channel_pool.acquire() as channel:
            queue = await channel.declare_queue(name=queue, durable=True, passive=True, timeout=60)
            return queue.declaration_result.message_count

    @retry_exception
    async def close(self):
        await self.channel_pool.close()
        await self.connection.close()
