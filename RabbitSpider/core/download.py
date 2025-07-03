import random
from user_agents import parse
from RabbitSpider import Response
from curl_cffi import CurlHttpVersion
from curl_cffi.requests import BrowserType
from curl_cffi.requests import AsyncSession
from RabbitSpider.exceptions import RabbitExpect


class CurlDownload(object):
    def __init__(self):
        self.impersonate = None
        self.default_headers = False
        self.http_version = CurlHttpVersion.V2TLS

    async def fetch(self, session: AsyncSession, request: dict) -> Response:
        if not (len(session.headers.keys()) or request.get('headers')):
            self.default_headers = True
            self.impersonate = random.choice(list(BrowserType)).value
        else:
            user_agent = session.headers.get('user-agent') or request.get('headers').get('user-agent')
            ua = parse(user_agent)
            browser_type = (ua.browser.family + ua.browser.version_string).lower().split('.')[0]
            if browser_type in BrowserType:
                self.impersonate = browser_type

        if request['method'].upper() == 'GET':
            res = await session.get(request['url'],
                                    params=request.get('params'), cookies=request.get('cookies'),
                                    headers=request.get('headers'), proxy=request.get('proxy'),
                                    allow_redirects=request.get('allow_redirects', True),
                                    http_version=self.http_version,
                                    impersonate=self.impersonate,
                                    timeout=request.get('timeout'),
                                    default_headers=self.default_headers
                                    )

        elif request['method'].upper() == 'POST':
            res = await session.post(request['url'],
                                     data=request.get('data'), json=request.get('json'),
                                     cookies=request.get('cookies'), headers=request.get('headers'),
                                     proxy=request.get('proxy'),
                                     http_version=self.http_version,
                                     impersonate=self.impersonate,
                                     allow_redirects=request.get('allow_redirects', True),
                                     timeout=request.get('timeout'),
                                     default_headers=self.default_headers
                                     )

        else:
            raise RabbitExpect(f"{request['method']}请求方式未定义，请自定义添加！")

        if res:
            return Response(res.status_code, res.headers, res.cookies, res.charset, res.content)
