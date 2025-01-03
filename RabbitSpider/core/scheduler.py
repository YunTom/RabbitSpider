import pickle
from typing import Callable, Optional
from aio_pika import connect_robust, Message, pool
from aio_pika.exceptions import ConnectionClosed, ChannelClosed, AMQPConnectionError


class Scheduler(object):
    def __init__(self, logger, settings):
        self.connection = None
        self.channel_pool = None
        self.logger = logger
        self.channel_size = settings.get('CHANNEL_SIZE')
        self.username = settings.get('RABBIT_USERNAME')
        self.password = settings.get('RABBIT_PASSWORD')
        self.host = settings.get('RABBIT_HOST')
        self.port = settings.get('RABBIT_PORT')
        self.virtual_host = settings.get('RABBIT_VIRTUAL_HOST')

    @staticmethod
    def retry_connect(function):
        async def wrapper(self, *args, **kwargs):
            for i in range(5):
                try:
                    return await function(self, *args, **kwargs)
                except ConnectionClosed or ChannelClosed or AMQPConnectionError:
                    await self.connect()
                    self.logger.warning('RabbitMq 重新连接！')
                except Exception as exc:
                    self.logger.error(exc.__class__.__name__)
            else:
                self.logger.error('RabbitMq 连接失败！')

        return wrapper

    @retry_connect
    async def connect(self):
        self.connection = await connect_robust(host=self.host, login=self.username, password=self.password,
                                               virtualhost=self.virtual_host)
        self.channel_pool = pool.Pool(self.connection.channel, max_size=self.channel_size)

    @retry_connect
    async def create_queue(self, queue: str):
        async with self.channel_pool.acquire() as channel:
            await channel.declare_queue(name=queue, durable=True, arguments={"x-max-priority": 10})

    @retry_connect
    async def producer(self, queue: str, body: dict):
        ret = pickle.dumps(body)
        async with self.channel_pool.acquire() as channel:
            await channel.default_exchange.publish(
                Message(body=ret, delivery_mode=2, priority=body['retry_times']), routing_key=queue)

    @retry_connect
    async def consumer(self, queue: str, callback: Optional[Callable] = None, prefetch: int = 1):
        async with self.channel_pool.acquire() as channel:
            queue = await channel.declare_queue(name=queue, durable=True, passive=True)
            if callback:
                await channel.set_qos(prefetch_count=prefetch)
                await queue.consume(callback=callback)
            else:
                return await queue.get(fail=False)

    @retry_connect
    async def queue_purge(self, queue: str):
        async with self.channel_pool.acquire() as channel:
            queue = await channel.declare_queue(name=queue, durable=True, passive=True)
            await queue.purge()

    @retry_connect
    async def delete_queue(self, queue: str):
        async with self.channel_pool.acquire() as channel:
            await channel.queue_delete(queue)

    @retry_connect
    async def get_message_count(self, queue: str):
        async with self.channel_pool.acquire() as channel:
            queue = await channel.declare_queue(name=queue, durable=True, passive=True)
            return queue.declaration_result.message_count

    @retry_connect
    async def close(self):
        await self.channel_pool.close()
        await self.connection.close()
