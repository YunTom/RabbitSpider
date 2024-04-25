import json as js
import chardet
import parsel
from w3lib.encoding import http_content_type_encoding, html_to_unicode


class Response:
    def __init__(self, content=None, status_code=None, charset=None, res=None):
        self.url = str(res.url)
        self.body = self.content = content
        self.status = self.status_code = status_code
        self.charset = charset
        self.res = res
        self.cookies = {k: v for k, v in self.res.cookies.items()}
        self.__r = parsel.Selector(self.text)

    def __str__(self):
        return self.text

    @property
    def text(self):
        if not self.content:
            return ''
        if self.charset:
            try:
                text = self.content.decode(self.charset)
            except UnicodeDecodeError:
                try:
                    benc = http_content_type_encoding(dict(self.res.headers)['Content-Type'])
                    if benc:
                        charset = 'charset=%s' % benc
                        text = html_to_unicode(charset, self.body)[1]
                    else:
                        raise UnicodeDecodeError
                except UnicodeDecodeError:
                    try:
                        char = chardet.detect(self.content)
                        if char:
                            text = self.content.decode(char['encoding'])
                        else:
                            raise UnicodeDecodeError
                    except UnicodeDecodeError:
                        try:
                            text = self.content.decode('utf-8')
                        except UnicodeDecodeError:
                            try:
                                text = self.content.decode("gb18030")
                            except UnicodeDecodeError:
                                text = self.content.decode('utf-8', "ignore")
        else:
            try:
                text = self.content.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    char = chardet.detect(self.content)
                    if char:
                        text = self.content.decode(char['encoding'])
                    else:
                        raise UnicodeDecodeError
                except UnicodeDecodeError:
                    try:
                        text = self.content.decode('gb18030')
                    except UnicodeDecodeError:
                        text = self.content.decode('utf-8', "ignore")
        return text

    def json(self):
        return js.loads(self.text, strict=False)

    def xpath(self, x):
        return self.__r.xpath(x)

    def css(self, x):
        return self.__r.css(x)
