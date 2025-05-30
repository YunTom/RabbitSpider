import re
import json
import chardet
import parsel
from w3lib.encoding import http_content_type_encoding, html_to_unicode


class Response:
    def __init__(self, status_code, headers, cookies, charset, content):
        self.content = content
        self.charset = charset
        self.status_code = status_code
        self.headers = {k: v for k, v in headers.items()}
        self.cookies = {k: v for k, v in cookies.items()}
        self.__r = parsel.Selector(self.text)

    @property
    def text(self):
        if not self.content:
            return ''
        if self.charset:
            try:
                text = self.content.decode(self.charset)
            except UnicodeDecodeError:
                try:
                    benc = http_content_type_encoding(self.headers['Content-Type'])
                    if benc:
                        charset = 'charset=%s' % benc
                        text = html_to_unicode(charset, self.content)[1]
                    else:
                        raise UnicodeDecodeError
                except (UnicodeDecodeError, KeyError):
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

    @property
    def json(self):
        result = re.findall(r'[.*?(]?(\[?{.*}]?)[).*]?', self.text, re.DOTALL)
        if result:
            return json.loads(result[0], strict=False)

    def xpath(self, x):
        return self.__r.xpath(x)

    def css(self, x):
        return self.__r.css(x)
