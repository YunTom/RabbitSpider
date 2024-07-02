import os
import sys
import redis
from RabbitSpider.dupefilters import DupeFilter


class RedisDupeFilter(DupeFilter):
    def __init__(self, settings):
        super().__init__(settings)
        self.repeat = os.path.basename(sys.argv[0])
        self.redis = redis.StrictRedis(host=settings.get('REDIS_HOST'), port=settings.get('REDIS_PORT'),
                                       db=settings.get('REDIS_DB'), password=settings.get('REDIS_PASSWORD'))
        self.redis.delete(self.repeat)

    def request_seen(self, fingerprint):
        if self.redis:
            result = self.redis.sadd(self.repeat, fingerprint)
            return result
