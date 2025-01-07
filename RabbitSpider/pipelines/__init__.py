from RabbitSpider.utils.log import Logger
from RabbitSpider.utils.control import SettingManager


class BasePipeline(object):
    def __init__(self, settings):
        self.logger = Logger(settings)
        self.settings: SettingManager = settings

    async def open_spider(self):
        """初始化数据库"""
        pass

    async def process_item(self, item, spider):
        """入库逻辑"""
        pass

    async def close_spider(self):
        """关闭连接"""
        pass
