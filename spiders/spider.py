from jsonpath import jsonpath
from RabbitSpider.core.engine import Engine
from RabbitSpider.http.request import Request
from RabbitSpider.http.response import Response
from RabbitSpider.utils.rabbit_go import go


class Test(Engine):

    async def start_requests(self):
        for i in range(100):
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
    go(Test, 'auto', 1, 3)
