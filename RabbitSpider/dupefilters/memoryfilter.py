from RabbitSpider.dupefilters import DupeFilter


class MemoryFilter(DupeFilter):
    def __init__(self, crawler):
        super().__init__(crawler)
        self.repeat = set()

    def request_seen(self, request):
        fingerprint = self.request_fingerprint(request)
        if fingerprint in self.repeat:
            return False
        else:
            self.repeat.add(fingerprint)
            return True
