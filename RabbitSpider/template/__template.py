import os
import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('create', default='create', help='参数：create')
    parser.add_argument('project', help='参数：项目名称')
    parser.add_argument('model', help='参数：文件名称')
    args = parser.parse_args()

    spider = f'''import asyncio
import os
from RabbitSpider.core.engine import Engine
from RabbitSpider.http.request import Request
from RabbitSpider.http.response import Response
from RabbitSpider.utils.rabbit_go import go
from {args.project}.items import {args.model.capitalize()}Item


class {args.model.capitalize()}(Engine):
    name = os.path.basename(__file__)
    async def start_requests(self):
        pass

    async def parse(self, request: Request, response: Response):
        pass


if __name__ == '__main__':
    asyncio.run(go({args.model.capitalize()}, 'auto', 10))
'''

    item = f'''from RabbitSpider.items import Item, Field


class {args.model.capitalize()}Item(Item):
    pass
'''

    middleware = f'''from RabbitSpider.middleware import BaseMiddleware


class {args.model.capitalize()}Middleware(BaseMiddleware):

    async def process_request(self, request, spider):
        """请求预处理"""
        pass

    async def process_response(self, request, response, spider):
        """响应预处理"""
        pass

    async def process_exception(self, request, exc, spider):
        """异常预处理"""
        pass
'''

    pipeline = f'''from RabbitSpider.pipelines import BasePipeline


class {args.model.capitalize()}Pipeline(BasePipeline):
    async def open_spider(self, spider):
        """初始化数据库"""
        pass

    async def process_item(self, item, spider):
        """入库逻辑"""
        spider.logger.info(item.to_dict())

    async def close_spider(self, spider):
        pass
'''

    setting = f'''# Rabbitmq
RABBIT_HOST = '127.0.0.1'
RABBIT_PORT = 5672
RABBIT_USERNAME = 'yuntom'
RABBIT_PASSWORD = '123456'
RABBIT_VIRTUAL_HOST = '/'

# redis 未配置默认使用set去重
REDIS_QUEUE_HOST = '127.0.0.1'
REDIS_QUEUE_PORT = 6379
REDIS_QUEUE_DB = 1

# 日志等级
LOG_LEVEL = 'ERROR'

# 中间件
MIDDLEWARES = ['middlewares.{args.model.capitalize()}Middleware']

# 管道
ITEM_PIPELINES = ['pipelines.{args.model.capitalize()}Pipeline']

# 最大重试次数
MAX_RETRY = 5
'''
    if not os.path.exists(os.path.join(os.getcwd(), f'{args.project}')):
        os.makedirs(f'./{args.project}/spiders/')
        with open(rf'./{args.project}/__init__.py', 'w', encoding='utf-8') as f:
            pass
        with open(rf'./{args.project}/spiders/__init__.py', 'w', encoding='utf-8') as f:
            pass
        with open(rf'./{args.project}/spiders/{args.model}.py', 'w', encoding='utf-8') as f:
            f.write(spider)
        with open(rf'./{args.project}/items.py', 'w', encoding='utf-8') as f:
            f.write(item)
        with open(rf'./{args.project}/middlewares.py', 'w', encoding='utf-8') as f:
            f.write(middleware)
        with open(rf'./{args.project}/pipelines.py', 'w', encoding='utf-8') as f:
            f.write(pipeline)
        with open(rf'./{args.project}/settings.py', 'w', encoding='utf-8') as f:
            f.write(setting)
        print(f'{args.project}项目创建完成')
    else:
        print(f'目录{args.project}已存在')


if __name__ == '__main__':
    main()
