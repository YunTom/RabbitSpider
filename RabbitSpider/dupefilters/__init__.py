import json
import hashlib
from io import BytesIO
from RabbitSpider.http.request import Request
from urllib.parse import urlencode


class DupeFilter(object):
    def __init__(self, crawler):
        pass

    def request_fingerprint(self, request: Request):
        if isinstance(request.data, (dict, list, tuple)):
            body = urlencode(request.data).encode('utf-8')
        elif isinstance(request.data, str):
            body = request.data.encode('utf-8')
        elif isinstance(request.data, BytesIO):
            body = request.data.read()
        elif isinstance(request.data, bytes):
            body = request.data
        else:
            body = b""

        if request.json is not None:
            body = json.dumps(request.json, separators=(",", ":")).encode()

        sha1 = hashlib.sha1()
        if isinstance(request.params, (dict, list, tuple)):
            sha1.update(f'{request.url}?{urlencode(request.params)}'.encode('utf-8'))
        else:
            sha1.update(request.url.encode('utf-8'))
        sha1.update(request.method.encode('utf-8'))
        sha1.update(body)
        sha1.update(str(request.retry_times).encode('utf-8'))
        return sha1.hexdigest()

    def request_seen(self, request: Request) -> bool:
        pass
