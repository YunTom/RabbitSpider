import re
from typing import Callable, get_type_hints
from RabbitSpider.utils.exceptions import RabbitExpect


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
                 retry: int = 0,
                 meta: dict | None = None
                 ):
        self.url = url
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
        self.retry = retry
        self._meta = meta
        self.__argsValidators__({k: v for k, v in locals().items() if k not in ['self']})

    def __argsValidators__(self, kwargs):
        pattern = re.compile('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
        hints = get_type_hints(self.__init__)
        for key, value in kwargs.items():
            args_type = hints.get(key)
            if args_type:
                if not isinstance(value, args_type):
                    raise RabbitExpect(f"Request参数类型错误{key}")
            else:
                raise RabbitExpect(f"Request异常参数{key}")
        if not re.match(pattern, kwargs['url']):
            raise RabbitExpect(f'请检查url是否正确{kwargs["url"]}')

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
            'retry': self.retry
        }
