from RabbitSpider.http.request import Request


class DupeFilter(object):
    def __init__(self, *args, **kwargs):
        pass

    def request_seen(self, request: Request):
        pass
