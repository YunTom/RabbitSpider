from RabbitSpider import Request, Response
from RabbitSpider.utils.log import Logger
from RabbitSpider.utils import event


class Spider(object):
    name: str
    custom_settings: dict = {}

    def __init__(self):
        pass

    async def start_requests(self):
        """初始请求"""
        raise NotImplementedError

    async def parse(self, request: Request, response: Response):
        """默认回调"""
        pass

    def spider_opened(self, *args, **kwargs):
        pass

    def spider_closed(self, *args, **kwargs):
        pass

    def spider_error(self, *args, **kwargs):
        pass

    @classmethod
    def update_settings(cls, settings):
        settings.set_dict(cls.custom_settings)
        cls.logger = Logger(settings, cls.name)

    @classmethod
    def bind_event(cls, crawler):
        crawler.subscriber.subscribe(cls.spider_opened, event.spider_opened)
        crawler.subscriber.subscribe(cls.spider_closed, event.spider_closed)
        crawler.subscriber.subscribe(cls.spider_error, event.spider_error)
