import pickle
import hashlib
import redis


class RFPDupeFilter(object):
    def __init__(self, repeat, host,
                 port, db, password=None):
        if host:
            self.repeat = repeat
            self.redis = redis.StrictRedis(host=host, port=port, db=db, password=password)
            self.redis.delete(repeat)
        else:
            self.redis = None
            self.repeat = set()

    def request_seen(self, obj):
        fingerprint = hashlib.sha1(pickle.dumps(obj)).hexdigest()
        data = pickle.dumps(fingerprint)
        if self.redis:
            result = self.redis.sadd(self.repeat, data)
            return result
        else:
            if data in self.repeat:
                return False
            else:
                self.repeat.add(data)
                return True
