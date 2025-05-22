import pickle
from typing import Callable, Optional
from aio_pika import connect_robust, Message, pool
from aio_pika.exceptions import ChannelNotFoundEntity


class Scheduler(object):
    def __init__(self, settings):
        self.connection = None
        self.channel_pool = None
        self.host = settings.get('RABBIT_HOST')
        self.port = settings.get('RABBIT_PORT')
        self.username = settings.get('RABBIT_USERNAME')
        self.password = settings.get('RABBIT_PASSWORD')
        self.channel_size = settings.get('CHANNEL_SIZE')
        self.virtual_host = settings.get('RABBIT_VIRTUAL_HOST')

    async def connect(self):
        self.connection = await connect_robust(host=self.host, login=self.username, password=self.password,
                                               virtualhost=self.virtual_host, heartbeat=30, timeout=60)
        self.channel_pool = pool.Pool(self.connection.channel, max_size=self.channel_size)

    async def create_queue(self, queue: str):
        async with self.channel_pool.acquire() as channel:
            await channel.declare_queue(name=queue, durable=True, arguments={"x-max-priority": 10}, timeout=60)

    async def producer(self, queue: str, body: dict):
        ret = pickle.dumps(body)
        async with self.channel_pool.acquire() as channel:
            await channel.default_exchange.publish(
                Message(body=ret, delivery_mode=2, priority=body['retry_times']), routing_key=queue, timeout=60)

    async def consumer(self, spider, callback: Optional[Callable] = None, prefetch: int = 1):
        async with self.channel_pool.acquire() as channel:
            try:
                queue = await channel.declare_queue(name=spider.name, durable=True, passive=True, timeout=60)
            except ChannelNotFoundEntity:
                queue = await channel.declare_queue(name=spider.name, durable=True, arguments={"x-max-priority": 10},
                                                    timeout=60)
            if callback:
                await channel.set_qos(prefetch_count=prefetch)
                await queue.consume(callback=lambda incoming_message: callback(spider, incoming_message), timeout=60)
            else:
                return await queue.get(fail=False, timeout=60)

    async def queue_purge(self, queue: str):
        async with self.channel_pool.acquire() as channel:
            queue = await channel.declare_queue(name=queue, durable=True, passive=True, timeout=60)
            await queue.purge()

    async def delete_queue(self, queue: str):
        async with self.channel_pool.acquire() as channel:
            await channel.queue_delete(queue)

    async def get_message_count(self, queue: str):
        async with self.channel_pool.acquire() as channel:
            queue = await channel.declare_queue(name=queue, durable=True, passive=True, timeout=60)
            return queue.declaration_result.message_count

    async def close(self):
        await self.channel_pool.close()
        await self.connection.close()
