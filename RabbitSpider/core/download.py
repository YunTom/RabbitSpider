from curl_cffi.requests import AsyncSession
from RabbitSpider.http.response import Response


class CurlDownload(object):
    def __init__(self, http_version, impersonate):
        self.impersonate = impersonate
        self.http_version = http_version

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
                                    timeout=request.get('timeout', 60)
                                    )

        elif request['method'].upper() == 'POST':
            res = await session.post(request['url'],
                                     data=request.get('data', None), json=request.get('json', None),
                                     cookies=request.get('cookies', None), headers=request.get('headers', None),
                                     proxy=request.get('proxy', None),
                                     http_version=self.http_version,
                                     impersonate=self.impersonate,
                                     allow_redirects=request.get('allow_redirects', True),
                                     timeout=request.get('timeout', 180))

        else:
            raise "{%s}请求方式未定义，请自定义添加！" % request['method']

        if res:
            response = Response(res)
            return response
