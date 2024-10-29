基于rabbitmq 做消息队列开发的分布式协程爬虫框架，结构用法与scrapy类似

支持批量运行任务，运行模式 auto先生产后消费(适用于单机，运行完自动关闭任务)，m 只生产，w 只消费(一直监听任务)

使用curl_cffi封装的下载器，支持修改http版本，tls指纹

pip install RabbitSpider==2.7.1

创建项目cmd命令：
    rabbit create [项目名称] [目录名称] [爬虫文件名称]

自动创建爬虫项目模板
如：rabbit create shop xxx mama

    import asyncio
    from RabbitSpider import go
    from RabbitSpider import Request
    from RabbitSpider.spider import Spider
    
    
    class MamaSpider(Spider):
        name = '_'.join(__file__.replace('\\', '/').rsplit('/')[-2:]).split('.')[0]
        custom_settings = {}
    
        async def start_requests(self):
            yield Request(url='https://www.baidu.com')
    
        async def parse(self, request, response):
            pass
    
    
    if __name__ == '__main__':
        asyncio.run(go(MamaSpider, 'auto', 1))



