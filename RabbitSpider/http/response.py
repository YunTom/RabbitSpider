import json
import chardet
import parsel
from typing import Any
from io import BytesIO
from collections.abc import AsyncIterator, Mapping
from w3lib.encoding import http_content_type_encoding, html_to_unicode


class Response:

    def __init__(
            self,
            res: Any,
            status_code: int,
            headers: Mapping[str, str],
            cookies: Mapping[str, str],
            content: bytes,
            charset: str | None = None,
            stream: bool = False,
    ) -> None:
        self.res = res
        self.status_code = status_code
        self.headers = dict(headers)
        self.cookies = dict(cookies)
        self.content = content
        self.charset = charset
        self.stream = stream

        self._text: str | None = None
        self._selector: parsel.Selector | None = None

    async def aiter_bytes(self, chunk_size: int | None = None) -> AsyncIterator[bytes]:
        if self.stream:
            async for chunk in self.res.aiter_content(chunk_size):
                if chunk:
                    yield chunk
            return

        if self.content:
            yield self.content

    async def to_bytes_io(self, chunk_size: int | None = None) -> BytesIO:
        buffer = BytesIO()
        async for chunk in self.aiter_bytes(chunk_size):
            buffer.write(chunk)
        buffer.seek(0)
        return buffer

    @property
    def text(self) -> str:
        """
        优先级：
        1. 指定 charset
        2. HTTP header charset
        3. chardet 自动检测
        4. utf-8
        5. gb18030
        """
        if self._text is not None:
            return self._text

        content = self.content
        if not content:
            self._text = ""
            return self._text

        if self.charset:
            try:
                self._text = content.decode(self.charset)
                return self._text
            except (UnicodeDecodeError, LookupError):
                pass

        header_charset = http_content_type_encoding(
            self.headers.get("Content-Type", "")
        )
        if header_charset:
            try:
                _, self._text = html_to_unicode(
                    f"charset={header_charset}",
                    content,
                )
                return self._text
            except Exception:
                pass

        detected = chardet.detect(content)
        encoding = detected.get("encoding")

        for enc in (encoding, "utf-8", "gb18030"):
            if not enc:
                continue

            try:
                self._text = content.decode(enc)
                return self._text
            except (UnicodeDecodeError, LookupError):
                continue

        self._text = content.decode("utf-8", errors="ignore")
        return self._text

    @property
    def selector(self) -> parsel.Selector:
        if self._selector is None:
            self._selector = parsel.Selector(self.text)
        return self._selector

    def xpath(self, query: str) -> parsel.SelectorList:
        return self.selector.xpath(query)

    def css(self, query: str) -> parsel.SelectorList:
        return self.selector.css(query)

    @property
    def json(self) -> Any:
        text = self.text.strip()
        if not text:
            return None

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return []
