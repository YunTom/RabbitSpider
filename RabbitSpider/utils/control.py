import asyncio
from collections import defaultdict
from importlib import import_module
from asyncio import Task, Future, Semaphore
from RabbitSpider import Request, Response
from RabbitSpider import default_settings
from typing import Final, Dict, List, Callable
from RabbitSpider.core.download import CurlDownload


def load_class(_path):
    if not isinstance(_path, str):
        if callable(_path):
            return _path
        else:
            raise TypeError(f"args expected string or object, got {type(_path)}")
    module, name = _path.rsplit('.', 1)
    mod = import_module(module)
    try:
        cls = getattr(mod, name)
    except AttributeError:
        raise NameError(f"Module {module!r} doesn't define any project named {name!r}")

    return cls


class SettingManager(object):
    def __init__(self):
        try:
            settings = import_module('settings')
        except ModuleNotFoundError:
            settings = default_settings
        self.attribute = {}
        for key in dir(settings):
            if key.isupper():
                self.attribute[key] = getattr(settings, key)

    def __setitem__(self, key, value):
        self.attribute[key] = value

    def __getitem__(self, key):
        return self.attribute.get(key)

    def __delitem__(self, key):
        del self.attribute[key]

    def get(self, key, value=None):
        return self[key] if self[key] else value

    def getlist(self, key):
        return self[key] if self[key] else []

    def set(self, key, value):
        self[key] = value

    def update(self, custom_settings):
        self.attribute.update(custom_settings)


class TaskManager(object):
    def __init__(self, task_count: int):
        self.current_task: Final[set] = set()
        self.semaphore = Semaphore(task_count)

    def create_task(self, coroutine) -> Task:
        task = asyncio.create_task(coroutine)
        self.current_task.add(task)

        def done_callback(_fut: Future):
            self.current_task.remove(task)
            self.semaphore.release()

        task.add_done_callback(done_callback)
        return task

    def all_done(self):
        return len(self.current_task) == 0


class PipelineManager(object):
    def __init__(self, settings):
        self.settings = settings
        self.methods: Dict[str, List[Callable]] = defaultdict(list)
        self._add_pipe(settings.getlist('ITEM_PIPELINES'))

    def _add_pipe(self, pipelines):
        for pipeline in pipelines:
            pipeline_obj = load_class(pipeline)(self.settings)
            if hasattr(pipeline_obj, 'open_spider'):
                self.methods['open_spider'].append(getattr(pipeline_obj, 'open_spider'))
            if hasattr(pipeline_obj, 'process_item'):
                self.methods['process_item'].append(getattr(pipeline_obj, 'process_item'))
            if hasattr(pipeline_obj, 'close_spider'):
                self.methods['close_spider'].append(getattr(pipeline_obj, 'close_spider'))

    async def open_spider(self):
        for method in self.methods['open_spider']:
            await method()

    async def process_item(self, req, spider):
        for method in self.methods['process_item']:
            await method(req, spider)

    async def close_spider(self):
        for method in self.methods['close_spider']:
            await method()


class MiddlewareManager(object):
    def __init__(self, settings):
        self.settings = settings
        self.download = CurlDownload()
        self.methods: Dict[str, List[Callable]] = defaultdict(list)
        self._add_middleware(settings.getlist('MIDDLEWARES'))

    def _add_middleware(self, middlewares):
        for middleware in middlewares:
            middleware_obj = load_class(middleware)(self.settings)
            if hasattr(middleware_obj, 'process_request'):
                self.methods['process_request'].append(getattr(middleware_obj, 'process_request'))
            if hasattr(middleware_obj, 'process_response'):
                self.methods['process_response'].append(getattr(middleware_obj, 'process_response'))
            if hasattr(middleware_obj, 'process_exception'):
                self.methods['process_exception'].append(getattr(middleware_obj, 'process_exception'))

    async def process_request(self, spider, request):
        for method in self.methods['process_request']:
            result = await method(request, spider)
            if isinstance(result, (Request, Response)):
                return result
            if result:
                break
        else:
            return await self.download.fetch(spider.session, request.to_dict())

    async def process_response(self, spider, request, response):
        for method in reversed(self.methods['process_response']):
            result = await method(request, response, spider)
            if isinstance(result, (Request, Response)):
                return result
            if result:
                break
        else:
            return response

    async def process_exception(self, spider, request, exc):
        for method in self.methods['process_exception']:
            result = await method(request, exc, spider)
            if isinstance(result, (Request, Response)):
                return result
            if result:
                break
        else:
            raise exc

    async def send(self, spider, request: Request):
        try:
            resp = await self.process_request(spider, request)
        except Exception as exc:
            resp = await self.process_exception(spider, request, exc)
        if isinstance(resp, Response):
            resp = await self.process_response(spider, request, resp)
        if isinstance(resp, Request):
            return request, None
        if not resp:
            return None, None
        return request, resp


class FilterManager(object):
    def __init__(self, settings):
        filter_cls = settings.get('DUPEFILTER_CLASS')
        if filter_cls:
            self.filter_obj = load_class(filter_cls)(settings)
        else:
            self.filter_obj = None

    def request_seen(self, request: Request) -> bool:
        if self.filter_obj:
            result = self.filter_obj.request_seen(request)
            return result
        else:
            return True
