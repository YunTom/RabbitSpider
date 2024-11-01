import re
from typing import Callable


class Request(object):
    def __init__(self,
                 url: str,
                 params: dict = None,
                 data: dict | str | bytes | None = None,
                 json: dict = None,
                 method: str = 'get',
                 headers: dict | None = None,
                 cookies: dict | None = None,
                 proxy: str | None = None,
                 timeout: int | None = None,
                 allow_redirects: bool = True,
                 callback: str | Callable = 'parse',
                 retry_times: int = 0,
                 meta: dict | None = None
                 ):
        self._url = url
        self.params = params
        self.data = data
        self.json = json
        self.method = method
        self.headers = headers
        self.cookies = cookies
        self.proxy = proxy
        self.timeout = timeout
        self.allow_redirects = allow_redirects
        self._callback = callback
        self.retry_times = retry_times
        self._meta = meta

    @property
    def url(self):
        pattern = re.compile('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
        if not re.match(pattern, self._url):
            raise ValueError(f'请检查url是否正确{self._url}')
        return self._url

    @property
    def meta(self):
        return self._meta if self._meta else {}

    @property
    def callback(self):
        return self._callback.__name__ if callable(self._callback) else self._callback

    def to_dict(self):
        return {
            'url': self.url,
            'params': self.params,
            'data': self.data,
            'json': self.json,
            'method': self.method,
            'headers': self.headers,
            'cookies': self.cookies,
            'proxy': self.proxy,
            'timeout': self.timeout,
            'allow_redirects': self.allow_redirects,
            'callback': self.callback,
            'meta': self.meta,
            'retry_times': self.retry_times
        }
