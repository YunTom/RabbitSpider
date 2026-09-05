import pickle
from RabbitSpider import settings
from typing import Any, Awaitable, Callable
from aio_pika.exceptions import ChannelNotFoundEntity
from aio_pika import connect_robust, Message, pool, IncomingMessage


class Scheduler:
    def __init__(self) -> None:
        self.connection: Any = None
        self.channel_pool: Any = None
        self.active_task_count: int = 0
        self.host = settings.get('RABBIT_HOST')
        self.port = settings.get('RABBIT_PORT')
        self.username = settings.get('RABBIT_USERNAME')
        self.password = settings.get('RABBIT_PASSWORD')
        self.channel_size = settings.get('CHANNEL_SIZE')
        self.virtual_host = settings.get('RABBIT_VIRTUAL_HOST')

    async def connect(self) -> None:
        self.connection = await connect_robust(host=self.host, port=self.port, login=self.username,
                                               password=self.password, virtualhost=self.virtual_host, heartbeat=60)
        self.channel_pool = pool.Pool(self.connection.channel, max_size=self.channel_size)

    async def create_queue(self, queue_name: str) -> None:
        async with self.channel_pool.acquire() as channel:
            await channel.declare_queue(name=queue_name, durable=True, arguments={"x-max-priority": 10})

    async def producer(self, queue_name: str, body: dict[str, Any]) -> None:
        payload = pickle.dumps(body)
        async with self.channel_pool.acquire() as channel:
            await channel.default_exchange.publish(
                Message(
                    body=payload,
                    content_type='application/python-pickle',
                    delivery_mode=2,
                    priority=body['retry_times'],
                ),
                routing_key=queue_name,
            )

    async def get_message(self, queue_name: str) -> dict[str, Any] | None:
        async with self.channel_pool.acquire() as channel:
            try:
                queue = await channel.declare_queue(name=queue_name, durable=True, passive=True)
            except ChannelNotFoundEntity:
                queue = await channel.declare_queue(name=queue_name, durable=True, arguments={"x-max-priority": 10},
                                                    )
            message = await queue.get(fail=False, no_ack=True, timeout=30)
            if message:
                return pickle.loads(message.body)

    async def consumer(
            self,
            spider: Any,
            callback: Callable[[dict[str, Any]], Awaitable[None]],
            prefetch: int = 1,
    ) -> None:
        channel = await self.connection.channel()
        try:
            queue = await channel.declare_queue(name=spider.name, durable=True, passive=True)
        except ChannelNotFoundEntity:
            queue = await channel.declare_queue(name=spider.name, durable=True, arguments={"x-max-priority": 10})
        await channel.set_qos(prefetch_count=prefetch)

        async def _callback(message: IncomingMessage) -> None:
            self.active_task_count += 1
            try:
                async with message.process():
                    data = pickle.loads(message.body)
                    await callback(data)
            finally:
                self.active_task_count -= 1

        await queue.consume(callback=_callback)

    async def queue_purge(self, queue_name: str) -> None:
        async with self.channel_pool.acquire() as channel:
            queue = await channel.declare_queue(name=queue_name, durable=True, passive=True)
            await queue.purge()

    async def delete_queue(self, queue_name: str) -> None:
        async with self.channel_pool.acquire() as channel:
            await channel.queue_delete(queue_name)

    async def get_message_count(self, queue_name: str) -> int:
        async with self.channel_pool.acquire() as channel:
            queue = await channel.declare_queue(name=queue_name, durable=True, passive=True)
            return queue.declaration_result.message_count

    async def is_queue_empty(self, queue_name: str) -> bool:
        return not await self.get_message_count(queue_name)

    async def close(self) -> None:
        try:
            await self.channel_pool.close()
            await self.connection.close()
        except Exception:
            pass
