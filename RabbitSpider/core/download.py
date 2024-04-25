from curl_cffi.requests import AsyncSession
from RabbitSpider.http.response import Response


class CurlDownload(object):
    def __init__(self, http2, impersonate):
        self.impersonate = impersonate
        if http2:
            self.http_version = 2
        else:
            self.http_version = None

    @staticmethod
    async def new_session():
        session = AsyncSession(verify=False)
        return session

    @staticmethod
    async def exit(session):
        await session.close()

    async def fetch(self, session, request):
        if request['method'].upper() == 'GET':
            res = await session.get(request['url'],
                                    params=request.get('params', None), cookies=request.get('cookies', None),
                                    headers=request.get('headers', None), proxy=request.get('proxy', None),
                                    allow_redirects=request.get('allow_redirects', True),
                                    http_version=self.http_version,
                                    impersonate=self.impersonate,
                                    timeout=request.get('timeout', 10)
                                    )

        elif request['method'].upper() == 'POST':
            res = await session.post(request['url'],
                                     data=request.get('data', None), json=request.get('json', None),
                                     cookies=request.get('cookies', None), headers=request.get('headers', None),
                                     proxy=request.get('proxies', None),
                                     http_version=self.http_version,
                                     impersonate=self.impersonate,
                                     allow_redirects=request.get('allow_redirects', True),
                                     timeout=request.get('timeout', 180))

        else:
            raise "{%s}请求方式未定义，请自定义添加！" % request['method']

        if res:
            content = res.content
            status_code = res.status_code
            charset = res.charset
            response = Response(
                content, status_code, charset, res)
            return response
