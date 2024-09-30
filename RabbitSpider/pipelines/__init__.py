from RabbitSpider.utils import event


class BasePipeline(object):
    def __init__(self, crawler):
        crawler.subscriber.subscribe(self.open_spider, event.spider_opened)
        crawler.subscriber.subscribe(self.process_item, event.spider_item)
        crawler.subscriber.subscribe(self.close_spider, event.spider_closed)

    async def open_spider(self, spider):
        """初始化数据库"""
        pass

    async def process_item(self, item, spider):
        """入库逻辑"""
        pass

    async def close_spider(self, spider):
        """关闭连接"""
        pass

    @classmethod
    def create_instance(cls, crawler):
        return cls(crawler)
