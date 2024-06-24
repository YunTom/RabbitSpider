import pickle
import hashlib
from io import BytesIO
import json
from RabbitSpider.dupefilters import DupeFilter
from urllib.parse import urlencode


class SetDupeFilter(DupeFilter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.repeat = set()

    def request_seen(self, request):
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
        sha1.update(str(request.retry).encode('utf-8'))
        fingerprint = sha1.hexdigest()
        data = pickle.dumps(fingerprint)
        if data in self.repeat:
            return False
        else:
            self.repeat.add(data)
            return True
