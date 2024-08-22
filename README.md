基于rabbitmq 做消息队列开发的分布式协程爬虫框架，结构用法与scrapy类似

支持批量运行任务，运行模式 auto(适用于单机，运行完自动关闭任务)先生产后消费，m 只生产，w 只消费(一直监听任务)

vue搭建的爬虫web管理，支持部署任务（基于crontab定时），实时监控，删除任务

使用curl_cffi封装的下载器，支持修改http版本，tls指纹

pip install RabbitSpider==2.6.0

创建项目命令：
    rabbit create [项目名称] [爬虫文件名称]

如：rabbit create emmo momo

    import os, asyncio
    from RabbitSpider import Engine
    from RabbitSpider import Request
    from RabbitSpider.rabbit_execute import go
    from jsonpath import jsonpath
    from emmo.items import Item


    class Momo(Engine):
        name = os.path.basename(__file__)
        custom_settings = {}
    
        async def start_requests(self):
            data = '{"token":"","pn":0,"rn":10,"sdt":"","edt":"","wd":"","inc_wd":"","exc_wd":"","fields":"","cnum":"",' \
                   '"sort":"{\\"webdate\\":\\"0\\",\\"id\\":\\"0\\"}","ssort":"","cl":10000,"terminal":"","condition":[{' \
                   '"fieldName":"categorynum","equal":"002006","notEqual":null,"equalList":null,"notEqualList":null,' \
                   '"isLike":true,"likeType":2}],"time":[{"fieldName":"webdate","startTime":"2024-01-25 00:00:00",' \
                   '"endTime":"2024-02-24 23:59:59"}],"highlights":"","statistics":null,"unionCondition":[],' \
                   '"accuracy":"","noParticiple":"1","searchRange":null,"noWd":true} '
    
            yield Request(url='https://www.jxsggzy.cn/XZinterface/rest/esinteligentsearch/getFullTextDataNew',
                          data=data, method='post')
    
        async def parse(self, request, response):
            url = 'https://www.jxsggzy.cn/' + jsonpath(response.json(), expr='$..linkurl')[0]
            yield Request(url=url, dupe_filter=False, callback=self.parse_item)
    
        async def parse_item(self, request, response):
            item = Item()
            item['title'] = response.xpath('//p[@class="title"]/text()').get()
            yield item
    
    
    if __name__ == '__main__':
        asyncio.run(go(Momo, 'auto', 10))


