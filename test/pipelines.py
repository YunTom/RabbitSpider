from RabbitSpider.pipelines import BasePipeline


class TestPipeline(BasePipeline):
    async def open_spider(self, spider):
        """初始化数据库"""
        pass

    async def process_item(self, item, spider):
        """入库逻辑"""
        spider.logger.info(item)

    async def close_spider(self, spider):
        pass
