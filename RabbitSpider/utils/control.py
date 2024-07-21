import asyncio
from collections import defaultdict
from importlib import import_module
from inspect import iscoroutinefunction
from typing import Final, Dict, List, Callable
from asyncio import Task, Future, Semaphore
from RabbitSpider import default_settings
from RabbitSpider.http.request import Request
from RabbitSpider.http.response import Response
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
    except AttributeError as exc:
        raise NameError(f"Module {module!r} doesn't define any project named {name!r}")

    return cls


async def call_function(func, *args, **kwargs):
    if iscoroutinefunction(func):
        return await func(*args, **kwargs)
    else:
        return func(*args, **kwargs)


class SettingManager(object):
    def __init__(self, custom_settings: dict):
        try:
            settings = import_module('settings')
        except ModuleNotFoundError:
            settings = default_settings
        self.attribute = {}
        for key in dir(settings):
            if key.isupper():
                self.attribute[key] = getattr(settings, key)
        self.attribute.update(custom_settings)

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
    def __init__(self, spider):
        self.spider = spider
        self.methods: Dict[str, List[Callable]] = defaultdict(list)
        self._add_pipe(spider.settings.getlist('ITEM_PIPELINES'))

    def _add_pipe(self, pipelines):
        for pipeline in pipelines:
            pipeline_obj = load_class(pipeline).create_instance(self.spider)
            if hasattr(pipeline_obj, 'open_spider'):
                self.methods['open_spider'].append(getattr(pipeline_obj, 'open_spider'))
            if hasattr(pipeline_obj, 'process_item'):
                self.methods['process_item'].append(getattr(pipeline_obj, 'process_item'))
            if hasattr(pipeline_obj, 'close_spider'):
                self.methods['close_spider'].append(getattr(pipeline_obj, 'close_spider'))

    async def open_spider(self):
        for method in self.methods['open_spider']:
            await call_function(method, self.spider)

    async def process_item(self, req):
        for method in self.methods['process_item']:
            await call_function(method, req, self.spider)

    async def close_spider(self):
        for method in self.methods['close_spider']:
            await call_function(method, self.spider)

    @classmethod
    def create_instance(cls, spider):
        return cls(spider)


class MiddlewareManager(object):
    def __init__(self, spider):
        self.spider = spider
        self.download = CurlDownload(spider.settings.get('HTTP_VERSION'), spider.settings.get('IMPERSONATE'))
        self.methods: Dict[str, List[Callable]] = defaultdict(list)
        self._add_middleware(spider.settings.getlist('MIDDLEWARES'))

    def _add_middleware(self, middlewares):
        for middleware in middlewares:
            middleware_obj = load_class(middleware).create_instance(self.spider)
            if hasattr(middleware_obj, 'process_request'):
                self.methods['process_request'].append(getattr(middleware_obj, 'process_request'))
            if hasattr(middleware_obj, 'process_response'):
                self.methods['process_response'].append(getattr(middleware_obj, 'process_response'))
            if hasattr(middleware_obj, 'process_exception'):
                self.methods['process_exception'].append(getattr(middleware_obj, 'process_exception'))

    async def _process_request(self, request):
        for method in self.methods['process_request']:
            result = await call_function(method, request, self.spider)
            if isinstance(result, (Request, Response)):
                return result
            if result:
                break
        else:
            return await self.download.fetch(self.spider.session, request.model_dump())

    async def _process_response(self, request, response):
        for method in reversed(self.methods['process_response']):
            result = await call_function(method, request, response, self.spider)
            if isinstance(result, (Request, Response)):
                return result
            if result:
                break
        else:
            return response

    async def _process_exception(self, request, exc):
        for method in self.methods['process_exception']:
            result = await call_function(method, request, exc, self.spider)
            if isinstance(result, (Request, Response)):
                return result
            if result:
                break
        else:
            raise exc

    async def downloader(self, request: Request):
        try:
            resp = await self._process_request(request)
        except Exception as exc:
            resp = await self._process_exception(request, exc)
        if isinstance(resp, Response):
            resp = await self._process_response(request, resp)
        if isinstance(resp, Request):
            return await self.spider.routing(resp)
        return request, resp

    @classmethod
    def create_instance(cls, spider):
        return cls(spider)


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
