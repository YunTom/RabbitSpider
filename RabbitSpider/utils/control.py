import asyncio
from typing import Final
from asyncio import Task, Future, Semaphore
from RabbitSpider import settings


class SettingManager(object):
    def __init__(self):
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
