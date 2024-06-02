import asyncio
from collections import defaultdict
from importlib import import_module
from typing import Final, Dict, List, Callable
from asyncio import Task, Future, Semaphore


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


class SettingManager(object):
    def __init__(self):
        settings = import_module('settings')
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

    def get(self, key):
        return self[key] if self[key] else None

    def set(self, key, value):
        self[key] = value


class TaskManager(object):
    def __init__(self, sync: int):
        self.current_task: Final[set] = set()
        self.semaphore = Semaphore(sync)

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
        self.methods: Dict[str, List[Callable]] = defaultdict(list)
        pipeline = spider.settings.get('ITEM_PIPELINES')
        self._add_pipe(pipeline)

    def _add_pipe(self, pipeline):
        pipe_obj = load_class(pipeline)()
        if hasattr(pipe_obj, 'open_spider'):
            self.methods['open_spider'] = getattr(pipe_obj, 'open_spider')
        if hasattr(pipe_obj, 'process_item'):
            self.methods['process_item'] = getattr(pipe_obj, 'process_item')
        if hasattr(pipe_obj, 'close_spider'):
            self.methods['close_spider'] = getattr(pipe_obj, 'close_spider')

    @classmethod
    def create_instance(cls, spider):
        return cls(spider)
