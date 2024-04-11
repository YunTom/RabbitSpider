基于rabbitmq 做消息队列开发的分布式异步爬虫框架，支持web监控，定时任务，运行模式 auto 先生产后消费，m 只生产，w 只消费

安装pip install RabbitSpider==1.3.0

    from jsonpath import jsonpath
    from RabbitSpider.core.engine import Engine
    from RabbitSpider.http.request import Request
    from RabbitSpider.http.response import Response
    from RabbitSpider.utils.rabbit_go import go


    class Test(Engine):
    
        def __init__(self, sync):
            super().__init__(sync)
            # pip 安装需要添加rabbitmq redis 配置
            self.settings.set('RABBIT_HOST', '121.36.225.245')
            self.settings.set('RABBIT_PORT', 5672)
            self.settings.set('RABBIT_USERNAME', 'yuntom')
            self.settings.set('RABBIT_PASSWORD', '123456')
            self.settings.set('RABBIT_VIRTUAL_HOST', '/')
            self.settings.set('REDIS_FILTER_NAME', 'filter_queue')
            self.settings.set('REDIS_QUEUE_HOST', '127.0.0.1')
            self.settings.set('REDIS_QUEUE_PORT', 6379)
            self.settings.set('REDIS_QUEUE_DB', 1)
    
        async def start_requests(self):
            for i in range(50):
                data = '{"token":"","pn":0,"rn":10,"sdt":"","edt":"","wd":"","inc_wd":"","exc_wd":"","fields":"","cnum":"","sort":"{\\"webdate\\":\\"0\\",\\"id\\":\\"0\\"}","ssort":"","cl":10000,"terminal":"","condition":[{"fieldName":"categorynum","equal":"002006","notEqual":null,"equalList":null,"notEqualList":null,"isLike":true,"likeType":2}],"time":[{"fieldName":"webdate","startTime":"2024-01-25 00:00:00","endTime":"2024-02-24 23:59:59"}],"highlights":"","statistics":null,"unionCondition":[],"accuracy":"","noParticiple":"1","searchRange":null,"noWd":true}'
                yield Request(url='https://www.jxsggzy.cn/XZinterface/rest/esinteligentsearch/getFullTextDataNew',
                              data=data, method='post', dupe_filter=False)
    
        async def parse(self, request: Request, response: Response):
            url = 'https://www.jxsggzy.cn/' + jsonpath(response.json(), expr='$..linkurl')[0]
            yield Request(url=url, dupe_filter=False, callback=self.parse_item)
    
        async def parse_item(self, request: Request, response: Response):
            item = {'title': response.xpath('//p[@class="title"]/text()').get()}
            yield item
    
        async def save_item(self, item: dict):
            """入库逻辑"""
            print(item)
    
    
    if __name__ == '__main__':
        go(Test, 'auto', 10)

