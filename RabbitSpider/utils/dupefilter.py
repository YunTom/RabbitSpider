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

    def request_seen(self, obj: dict):
        sha1 = hashlib.sha1()
        sha1.update(obj.get('url').encode('utf-8'))
        sha1.update(obj.get('method').encode('utf-8'))
        sha1.update(str(obj.get('params')).encode('utf-8') or b'')
        sha1.update(str(obj.get('data')).encode('utf-8') or b'')
        sha1.update(str(obj.get('json')).encode('utf-8') or b'')
        sha1.update(str(obj.get('retry')).encode('utf-8') or b'')
        fingerprint = sha1.hexdigest()
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
