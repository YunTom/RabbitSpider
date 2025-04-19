from RabbitSpider import Response
from curl_cffi import CurlHttpVersion
from RabbitSpider.exceptions import RabbitExpect


class CurlDownload(object):
    def __init__(self):
        self.impersonate = 'chrome120'
        self.http_version = CurlHttpVersion.V2TLS

    async def fetch(self, session, request) -> Response:
        if request['method'].upper() == 'GET':
            res = await session.get(request['url'],
                                    params=request.get('params', None), cookies=request.get('cookies', None),
                                    headers=request.get('headers', None), proxy=request.get('proxy', None),
                                    allow_redirects=request.get('allow_redirects', True),
                                    http_version=self.http_version,
                                    impersonate=self.impersonate,
                                    timeout=request.get('timeout', 30)
                                    )

        elif request['method'].upper() == 'POST':
            res = await session.post(request['url'],
                                     data=request.get('data', None), json=request.get('json', None),
                                     cookies=request.get('cookies', None), headers=request.get('headers', None),
                                     proxy=request.get('proxy', None),
                                     http_version=self.http_version,
                                     impersonate=self.impersonate,
                                     allow_redirects=request.get('allow_redirects', True),
                                     timeout=request.get('timeout', 60))

        else:
            raise RabbitExpect(f"{request['method']}请求方式未定义，请自定义添加！")

        if res:
            return Response(res.status_code, res.headers, res.cookies, res.charset, res.content)
