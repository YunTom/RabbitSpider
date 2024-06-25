基于rabbitmq 做消息队列开发的分布式协程爬虫框架，支持web监控，定时任务，运行模式 auto(适用于单机，自动关闭任务) 先生产后消费，m 只生产，w 只消费(一直监听任务)

使用curl_cffi封装的下载器，支持修改http版本，tls指纹

pip install RabbitSpider==2.4

创建项目命令：
    rabbit create [项目名称] [爬虫文件名称]

    import asyncio
    from jsonpath import jsonpath
    from RabbitSpider.core.engine import Engine
    from RabbitSpider.http.request import Request
    from RabbitSpider.http.response import Response
    from RabbitSpider.utils.rabbit_go import go
    from test.items import TestItem
    
    
    class Test(Engine):
    
        async def start_requests(self):
            for i in range(6):
                data = '{"token":"","pn":0,"rn":10,"sdt":"","edt":"","wd":"","inc_wd":"","exc_wd":"","fields":"","cnum":"","sort":"{\\"webdate\\":\\"0\\",\\"id\\":\\"0\\"}","ssort":"","cl":10000,"terminal":"","condition":[{"fieldName":"categorynum","equal":"002006","notEqual":null,"equalList":null,"notEqualList":null,"isLike":true,"likeType":2}],"time":[{"fieldName":"webdate","startTime":"2024-01-25 00:00:00","endTime":"2024-02-24 23:59:59"}],"highlights":"","statistics":null,"unionCondition":[],"accuracy":"","noParticiple":"1","searchRange":null,"noWd":true}'
                yield Request(url='https://www.jxsggzy.cn/XZinterface/rest/esinteligentsearch/getFullTextDataNew',
                              data=data, method='post', dupe_filter=False)
    
        async def parse(self, request: Request, response: Response):
            url = 'https://www.jxsggzy.cn/' + jsonpath(response.json(), expr='$..linkurl')[0]
            yield Request(url=url, dupe_filter=False, callback=self.parse_item)
    
        async def parse_item(self, request: Request, response: Response):
            item = TestItem()
            item['title'] = response.xpath('//p[@class="title"]/text()').get()
            yield item
    
    
    if __name__ == '__main__':
        asyncio.run(go(Test, 'auto', 10, 1))


