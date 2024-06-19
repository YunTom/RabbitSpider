class BasePipeline(object):
    def __init__(self, spider):
        pass

    async def open_spider(self, spider):
        """初始化数据库"""
        pass

    async def process_item(self, item, spider):
        """入库逻辑"""
        pass

    async def close_spider(self, spider):
        pass

    @classmethod
    def create_instance(cls, spider):
        return cls(spider)
