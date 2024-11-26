from RabbitSpider.utils.log import Logger


class BasePipeline(object):
    def __init__(self, crawler):
        self.logger: Logger = crawler.logger

    async def open_spider(self, spider):
        """初始化数据库"""
        pass

    async def process_item(self, item, spider):
        """入库逻辑"""
        pass

    async def close_spider(self, spider):
        """关闭连接"""
        pass
