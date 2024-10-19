import asyncio
from collections import defaultdict
from typing import Dict, Set, Callable


class Subscriber(object):
    def __init__(self):
        self._subscriber: Dict[str, Set[Callable]] = defaultdict(set)

    def subscribe(self, receiver: Callable, event: str):
        self._subscriber[event].add(receiver)

    def unsubscribe(self, receiver: Callable, event: str):
        self._subscriber[event].discard(receiver)

    async def notify(self, event: str, *args, **kwargs):
        await asyncio.gather(*[receiver(*args, **kwargs) for receiver in self._subscriber[event]])
