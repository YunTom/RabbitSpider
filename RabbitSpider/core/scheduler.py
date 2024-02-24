from aio_pika import connect, Message
from aio_pika.pool import Pool


class Scheduler(object):
    def __init__(self, username: str, password: str, host: str,
                 port: int, virtual_host: str):
        self.username = username
        self.password = password
        self.host = host
        self.port = port
        self.virtual_host = virtual_host

        async def get_connection():
            return await connect(host=self.host, login=self.username, password=self.password,
                                 virtualhost=self.virtual_host)

        self.connection_pool = Pool(get_connection, max_size=1)

        async def get_channel():
            async with self.connection_pool.acquire() as connection:
                return await connection.channel()

        self.channel_pool: Pool = Pool(get_channel, max_size=20)

    async def create_queue(self, queue: str):
        async with self.channel_pool.acquire() as channel:
            await channel.queue_delete(queue)
            await channel.declare_queue(name=queue, durable=True, arguments={"x-max-priority": 10})

    async def producer(self, queue: str, body: bytes, priority: int = 1):
        async with self.channel_pool.acquire() as channel:
            await channel.default_exchange.publish(Message(body=body, delivery_mode=2, priority=priority),
                                                   routing_key=queue)

    async def consumer(self, queue: str):
        async with self.channel_pool.acquire() as channel:
            queue = await channel.declare_queue(name=queue, durable=True, passive=True,
                                                arguments={"x-max-priority": 10})
            return await queue.get()

    async def delete_queue(self, queue: str):
        async with self.channel_pool.acquire() as channel:
            await channel.queue_delete(queue)
