from typing import Any
from types import TracebackType
from RabbitSpider import Response
from curl_cffi import CurlHttpVersion
from curl_cffi.requests import AsyncSession


class CurlHttpDownloader(object):
    def __init__(self):
        self.session = AsyncSession()

    async def __aenter__(self) -> "CurlHttpDownloader":
        return self

    async def __aexit__(self, exc_type: type[BaseException] | None,
                        exc_val: BaseException | None,
                        exc_tb: TracebackType | None):
        await self.session.close()

    async def fetch(self, request: dict[str, Any]) -> Response:
        method = request['method'].upper()
        stream = request.get('stream', False)

        if method == 'GET':
            res = await self.session.request(url=request['url'],
                                             method=request['method'],
                                             params=request.get('params'),
                                             cookies=request.get('cookies'),
                                             headers=request.get('headers'),
                                             proxy=request.get('proxy'),
                                             timeout=request.get('timeout'),
                                             allow_redirects=request.get('allow_redirects', True),
                                             http_version=CurlHttpVersion.V2TLS,
                                             impersonate='chrome131',
                                             stream=stream,
                                             verify=False
                                             )
        elif method == 'POST':
            res = await self.session.request(url=request['url'],
                                             method=request['method'],
                                             params=request.get('params'),
                                             data=request.get('data'),
                                             json=request.get('json'),
                                             cookies=request.get('cookies'),
                                             headers=request.get('headers'),
                                             proxy=request.get('proxy'),
                                             timeout=request.get('timeout'),
                                             allow_redirects=request.get('allow_redirects', True),
                                             http_version=CurlHttpVersion.V2TLS,
                                             impersonate='chrome131',
                                             stream=stream,
                                             verify=False
                                             )
        else:
            raise ValueError(f"{request['method']} request method is not defined")

        content = b'' if stream else res.content
        return Response(res, res.status_code, res.headers, res.cookies, content, charset=res.charset,
                        stream=stream)
