import asyncio
import random
from typing import TYPE_CHECKING

from RabbitSpider import Request, settings
from RabbitSpider.interceptor import SignalDispatcher

if TYPE_CHECKING:
    from RabbitSpider.spider import BaseSpider


class DownloadDelay(SignalDispatcher):
    def __init__(self) -> None:
        self.download_delay = settings.get('DOWNLOAD_DELAY')

    async def request_received(self, spider: "BaseSpider", request: Request) -> None:
        if self.download_delay:
            delay = random.uniform(self.download_delay[0], self.download_delay[1])
            await asyncio.sleep(delay)
