from curl_cffi.requests import AsyncSession
from RabbitSpider import Response, Request
from RabbitSpider.utils.control import MiddlewareManager
from RabbitSpider.utils.exceptions import RabbitExpect


class CurlDownload(object):
    def __init__(self, crawler):
        self.crawler = crawler
        self.impersonate = crawler.settings.get('IMPERSONATE')
        self.http_version = crawler.settings.get('HTTP_VERSION')
        self.middlewares = MiddlewareManager.create_instance(crawler)
        self.session = AsyncSession(verify=False)

    async def fetch(self, request):
        if request['method'].upper() == 'GET':
            res = await self.session.get(request['url'],
                                         params=request.get('params', None), cookies=request.get('cookies', None),
                                         headers=request.get('headers', None), proxy=request.get('proxy', None),
                                         allow_redirects=request.get('allow_redirects', True),
                                         http_version=self.http_version,
                                         impersonate=self.impersonate,
                                         timeout=request.get('timeout', 60)
                                         )

        elif request['method'].upper() == 'POST':
            res = await self.session.post(request['url'],
                                          data=request.get('data', None), json=request.get('json', None),
                                          cookies=request.get('cookies', None), headers=request.get('headers', None),
                                          proxy=request.get('proxy', None),
                                          http_version=self.http_version,
                                          impersonate=self.impersonate,
                                          allow_redirects=request.get('allow_redirects', True),
                                          timeout=request.get('timeout', 180))

        else:
            raise RabbitExpect(f"{request['method']}请求方式未定义，请自定义添加！")

        if res:
            response = Response(res)
            return response

    async def send(self, request: Request):
        try:
            resp = await self.middlewares.process_request(self.fetch, request)
        except Exception as exc:
            resp = await self.middlewares.process_exception(request, exc)
        if isinstance(resp, Response):
            resp = await self.middlewares.process_response(request, resp)
        if isinstance(resp, Request):
            return request, None
        if not resp:
            return None, None
        return request, resp
