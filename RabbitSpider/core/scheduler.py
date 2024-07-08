import pickle
from typing import Callable, Optional
from aio_pika import connect_robust, Message


class Scheduler(object):
    def __init__(self, settings):
        self.username = settings.get('RABBIT_USERNAME')
        self.password = settings.get('RABBIT_PASSWORD')
        self.host = settings.get('RABBIT_HOST')
        self.port = settings.get('RABBIT_PORT')
        self.virtual_host = settings.get('RABBIT_VIRTUAL_HOST')

    async def connect(self):
        connection = await connect_robust(host=self.host, login=self.username, password=self.password,
                                          virtualhost=self.virtual_host)
        channel = await connection.channel()
        return connection, channel

    @staticmethod
    async def create_queue(channel, queue: str):
        await channel.declare_queue(name=queue, durable=True, arguments={"x-max-priority": 10})

    @staticmethod
    async def producer(channel, queue: str, body: dict):
        ret = pickle.dumps(body)
        await channel.default_exchange.publish(
            Message(body=ret, delivery_mode=2, priority=body['retry']), routing_key=queue)

    @staticmethod
    async def consumer(channel, queue: str, callback: Optional[Callable] = None, prefetch: int = 1):
        queue = await channel.declare_queue(name=queue, durable=True, passive=True, arguments={"x-max-priority": 10})
        if callback:
            await channel.set_qos(prefetch_count=prefetch)
            await queue.consume(callback=callback)
        else:
            return await queue.get()

    @staticmethod
    async def queue_purge(channel, queue: str):
        queue = await channel.declare_queue(name=queue, durable=True, passive=True, arguments={"x-max-priority": 10})
        await queue.purge()

    @staticmethod
    async def delete_queue(channel, queue: str):
        await channel.queue_delete(queue)

    @staticmethod
    async def get_message_count(channel, queue: str):
        queue = await channel.declare_queue(name=queue, durable=True, passive=True)
        return queue.declaration_result.message_count
