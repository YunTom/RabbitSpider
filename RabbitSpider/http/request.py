from typing import Any, Callable
from urllib.parse import urlparse


class Request:

    def __init__(
            self,
            url: str,
            params: dict[str, Any] | None = None,
            data: dict[str, Any] | str | None = None,
            json: dict[str, Any] | None = None,
            method: str = 'GET',
            headers: dict[str, str] | None = None,
            cookies: dict[str, str] | None = None,
            proxy: str | None = None,
            timeout: int = 60,
            allow_redirects: bool = True,
            callback: str | Callable[..., Any] = 'parse',
            retry_times: int = 0,
            meta: dict[str, Any] | None = None,
            stream: bool = False,
    ) -> None:
        self._url: str = url
        self.params: dict[str, Any] | None = params
        if isinstance(data, bytes):
            raise TypeError("data 不支持 bytes 类型")
        self.data: dict[str, Any] | str | None = data
        self.json: dict[str, Any] | None = json
        self.method: str = method.lower()
        self.headers: dict[str, str] | None = headers
        self.cookies: dict[str, str] | None = cookies
        self.proxy: str | None = proxy
        self.timeout: int = timeout
        self.allow_redirects: bool = allow_redirects
        self._callback: str | Callable[..., Any] = callback
        self.retry_times: int = retry_times
        self._meta: dict[str, Any] = meta or {}
        self.stream: bool = stream

    @property
    def url(self) -> str:
        parsed = urlparse(self._url)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            raise ValueError(f"请检查 URL 是否正确: {self._url}")
        return self._url

    @url.setter
    def url(self, value: str) -> None:
        self._url = value

    @property
    def meta(self) -> dict[str, Any]:
        """返回请求元数据"""
        return self._meta

    @property
    def callback(self) -> str:
        """返回回调函数名"""
        return self._callback.__name__ if callable(self._callback) else self._callback

    def to_dict(self) -> dict[str, Any]:
        """将请求对象序列化为字典"""
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
            'retry_times': self.retry_times,
            'stream': self.stream,
        }
