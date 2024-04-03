import pickle
import hashlib
import redis


class RFPDupeFilter(object):
    def __init__(self, repeat, host,
                 port, db, password=None):
        self.repeat = repeat
        self.redis = redis.StrictRedis(host=host, port=port, db=db, password=password)
        self.redis.delete(repeat)

    def request_seen(self, obj):
        fingerprint = hashlib.md5(obj).hexdigest()
        result = self.redis.sadd(self.repeat, pickle.dumps(fingerprint))
        return result
