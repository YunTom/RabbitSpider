import pickle
from typing import Callable, Optional
from aio_pika import connect_robust, Message, pool


class Scheduler(object):
    def __init__(self, settings):
        self.connection = None
        self.channel_pool = None
        self.channel_size = settings.get('CHANNEL_SIZE')
        self.username = settings.get('RABBIT_USERNAME')
        self.password = settings.get('RABBIT_PASSWORD')
        self.host = settings.get('RABBIT_HOST')
        self.port = settings.get('RABBIT_PORT')
        self.virtual_host = settings.get('RABBIT_VIRTUAL_HOST')

    async def connect(self):
        self.connection = await connect_robust(host=self.host, login=self.username, password=self.password,
                                               virtualhost=self.virtual_host)
        self.channel_pool = pool.Pool(self.connection.channel, max_size=self.channel_size)

    async def create_queue(self, queue: str):
        async with self.channel_pool.acquire() as channel:
            await channel.declare_queue(name=queue, durable=True, arguments={"x-max-priority": 10})

    async def producer(self, queue: str, body: dict):
        ret = pickle.dumps(body)
        async with self.channel_pool.acquire() as channel:
            await channel.default_exchange.publish(
                Message(body=ret, delivery_mode=2, priority=body['retry_times']), routing_key=queue)

    async def consumer(self, queue: str, callback: Optional[Callable] = None, prefetch: int = 1):
        async with self.channel_pool.acquire() as channel:
            queue = await channel.declare_queue(name=queue, durable=True, passive=True)
            if callback:
                await channel.set_qos(prefetch_count=prefetch)
                await queue.consume(callback=callback)
            else:
                return await queue.get()

    async def queue_purge(self, queue: str):
        async with self.channel_pool.acquire() as channel:
            queue = await channel.declare_queue(name=queue, durable=True, passive=True)
            await queue.purge()

    async def delete_queue(self, queue: str):
        async with self.channel_pool.acquire() as channel:
            await channel.queue_delete(queue)

    async def get_message_count(self, queue: str):
        async with self.channel_pool.acquire() as channel:
            queue = await channel.declare_queue(name=queue, durable=True, passive=True)
            return queue.declaration_result.message_count

    async def close(self):
        await self.channel_pool.close()
        await self.connection.close()
