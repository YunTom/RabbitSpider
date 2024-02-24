import aiohttp
from RabbitSpider.http.response import Response


class Download:
    @staticmethod
    async def fetch(session, request):
        if request['method'].upper() == 'GET':
            async with session.get(request['url'],
                                   params=request.get('params', None), cookies=request.get('cookies', None),
                                   headers=request.get('headers', None), proxy=request.get('proxy', None),
                                   allow_redirects=request.get('allow_redirects', True),
                                   timeout=request.get('timeout', 10)
                                   ) as res:
                text = await res.read()

        elif request['method'].upper() == 'POST':
            async with session.post(request['url'],
                                    data=request.get('data', None), json=request.get('json', None),
                                    cookies=request.get('cookies', None), headers=request.get('headers', None),
                                    proxy=request.get('proxies', None),
                                    allow_redirects=request.get('allow_redirects', True),
                                    timeout=request.get('timeout', 180)) as res:
                text = await res.read()
        else:
            raise "{%s}请求方式未定义，请自定义添加！" % request['method']

        if res:
            status_code = res.status
            charset = res.charset
            response = Response(
                text, status_code, charset, res)
            return response

    @staticmethod
    async def new_session(verify=False):
        connector = aiohttp.TCPConnector(ssl=verify)
        session = aiohttp.ClientSession(connector=connector, trust_env=True)
        return session

    @staticmethod
    async def exit(session):
        await session.close()
