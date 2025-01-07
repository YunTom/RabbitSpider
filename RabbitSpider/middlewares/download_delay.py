import asyncio
import random

from RabbitSpider.middlewares import BaseMiddleware


class DownloadDelayMiddleware(BaseMiddleware):
    def __init__(self, settings):
        super().__init__(settings)
        self.download_delay = settings.get('DOWNLOAD_DELAY')

    async def process_request(self, request, spider):
        if self.download_delay:
            delay = random.uniform(self.download_delay[0], self.download_delay[1])
            await asyncio.sleep(delay)
