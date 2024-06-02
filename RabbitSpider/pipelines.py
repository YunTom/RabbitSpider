class PipelineBase(object):

    async def open_spider(self):
        """初始化数据库"""
        pass

    async def process_item(self, item):
        """入库逻辑"""
        pass

    async def close_spider(self):
        pass
