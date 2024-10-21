from RabbitSpider import Request, Response
from RabbitSpider.utils.log import Logger
from RabbitSpider.utils import event


class Spider(object):
    name: str
    custom_settings: dict = {}

    def __init__(self, crawler):
        crawler.settings.update(self.custom_settings)
        crawler.subscriber.subscribe(self.spider_opened, event.spider_opened)
        crawler.subscriber.subscribe(self.spider_closed, event.spider_closed)
        crawler.subscriber.subscribe(self.spider_error, event.spider_error)
        self.logger = Logger(crawler.settings, self.name)

    async def start_requests(self):
        """初始请求"""
        raise NotImplementedError

    async def parse(self, request: Request, response: Response):
        """默认回调"""
        pass

    async def spider_opened(self, *args, **kwargs):
        pass

    async def spider_closed(self, *args, **kwargs):
        pass

    async def spider_error(self, *args, **kwargs):
        pass
