from RabbitSpider.pipelines import PipelineBase


class TestPipeline(PipelineBase):
    async def open_spider(self, spider):
        """初始化数据库"""
        pass

    async def process_item(self, item, spider):
        """入库逻辑"""
        print(item)

    async def close_spider(self, spider):
        pass
