import os
import pickle
import hashlib
import sys
from io import BytesIO
import redis
import json
from RabbitSpider.dupefilters import DupeFilter
from urllib.parse import urlencode


class RedisDupeFilter(DupeFilter):
    def __init__(self, settings):
        super().__init__(settings)
        self.sha1 = hashlib.sha1()
        repeat = os.path.basename(sys.argv[0])
        self.repeat = repeat
        self.redis = redis.StrictRedis(host=settings.get('REDIS_HOST'), port=settings.get('REDIS_PORT'),
                                       db=settings.get('REDIS_DB'), password=settings.get('REDIS_PASSWORD'))
        self.redis.delete(repeat)

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

        if isinstance(request.params, (dict, list, tuple)):
            self.sha1.update(f'{request.url}?{urlencode(request.params)}'.encode('utf-8'))
        else:
            self.sha1.update(request.url.encode('utf-8'))
        self.sha1.update(request.method.encode('utf-8'))
        self.sha1.update(body)
        self.sha1.update(str(request.retry).encode('utf-8'))
        fingerprint = self.sha1.hexdigest()
        data = pickle.dumps(fingerprint)
        if self.redis:
            result = self.redis.sadd(self.repeat, data)
            return result
