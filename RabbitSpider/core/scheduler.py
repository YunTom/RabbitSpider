import asyncio
from typing import Callable, Optional
from aio_pika import connect_robust, Message
from aio_pika.pool import Pool


class Scheduler(object):
    def __init__(self, username: str, password: str, host: str,
                 port: int, virtual_host: str):
        self.username = username
        self.password = password
        self.host = host
        self.port = port
        self.virtual_host = virtual_host

    def connect(self):
        connection_pool = Pool(self.get_connection, max_size=1)
        channel_pool = Pool(self.get_channel, connection_pool, max_size=3)
        return connection_pool, channel_pool

    async def get_connection(self):
        return await connect_robust(host=self.host, login=self.username, password=self.password,
                                    virtualhost=self.virtual_host)

    @staticmethod
    async def get_channel(connection_pool):
        async with connection_pool.acquire() as connection:
            return await connection.channel()

    @staticmethod
    async def create_queue(channel_pool, queue: str):
        async with channel_pool.acquire() as channel:
            queue = await channel.declare_queue(name=queue, durable=True,
                                                arguments={"x-max-priority": 10})
            await queue.purge()

    @staticmethod
    async def producer(channel_pool, queue: str, body: bytes, priority: int = 1):
        async with channel_pool.acquire() as channel:
            await channel.default_exchange.publish(Message(body=body, delivery_mode=2, priority=priority),
                                                   routing_key=queue)

    @staticmethod
    async def consumer(channel_pool, queue: str, callback: Optional[Callable] = None, prefetch: int = 1, args=None):
        async with channel_pool.acquire() as channel:

            queue = await channel.declare_queue(name=queue, durable=True, passive=True,
                                                arguments={"x-max-priority": 10})
            if callback:
                await channel.set_qos(prefetch_count=prefetch)
                await queue.consume(callback=lambda message: callback(message, args))
                await asyncio.Future()
            else:
                return await queue.get()

    @staticmethod
    async def delete_queue(channel_pool, queue: str):
        async with channel_pool.acquire() as channel:
            await channel.queue_delete(queue)
