import hashlib
import json
from typing import TYPE_CHECKING, Any
from redis.asyncio import Redis
from RabbitSpider.interceptor import SignalDispatcher
from RabbitSpider import Request, settings

if TYPE_CHECKING:
    from RabbitSpider.spider import BaseSpider


class RedisFilter(SignalDispatcher):

    def __init__(self) -> None:
        self.host = settings.get('REDIS_HOST')
        self.port = settings.get('REDIS_PORT')
        self.db = settings.get('REDIS_DB')
        self.password = settings.get('REDIS_PASSWORD')
        self.redis = Redis(host=self.host, port=self.port, db=self.password)

    async def request_scheduled(
            self,
            spider: "BaseSpider",
            request: Request,
    ) -> bool | None:

        fingerprint = self._generate_fingerprint(request)
        # 1 -> 新增成功，不重复
        # 0 -> 已经存在，重复
        added = await self.redis.sadd(spider.name, fingerprint)
        if added:
            await self.redis.expire(spider.name, 600)
        return added == 0

    async def spider_closed(self, spider: "BaseSpider"):
        await self.redis.delete(spider.name)

    @staticmethod
    def _canonical_bytes(value: Any) -> bytes:
        if value is None:
            return b""

        if isinstance(value, str):
            return value.encode("utf-8")

        if isinstance(value, dict):
            return json.dumps(
                value,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")

        raise TypeError(
            f"不支持的请求内容类型: {type(value).__name__}"
        )

    @staticmethod
    def _update_hash(
            sha1: Any,
            name: str,
            value: bytes,
    ) -> None:
        name_bytes = name.encode("utf-8")

        sha1.update(len(name_bytes).to_bytes(2, "big"))
        sha1.update(name_bytes)

        sha1.update(len(value).to_bytes(8, "big"))
        sha1.update(value)

    def _generate_fingerprint(self, request: Request) -> str:
        sha1 = hashlib.sha1()

        body = (
            request.json
            if request.json is not None
            else request.data
        )

        parts = {
            "method": request.method.upper().encode("utf-8"),
            "url": request.url.encode("utf-8"),
            "params": self._canonical_bytes(request.params),
            "body": self._canonical_bytes(body),
            "callback": request.callback.encode("utf-8"),
            "retry_times": str(request.retry_times).encode("utf-8"),
        }

        for name, value in parts.items():
            self._update_hash(sha1, name, value)

        return sha1.hexdigest()
