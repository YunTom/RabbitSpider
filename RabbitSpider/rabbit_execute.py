import sys
from typing import TypeVar
from RabbitSpider import settings
from RabbitSpider.spider import BaseSpider
from RabbitSpider.core.engine import Engine

T_Spider = TypeVar('T_Spider', bound=BaseSpider)


async def go(spider: type[T_Spider], mode: str = 'auto', task_count: int = 1) -> None:
    for i in sys.argv[1:]:
        key, value = i.split('=')
        if key == 'mode':
            mode = value
        if key == 'task_count':
            task_count = int(value)
    settings.set('MODE', mode)
    settings.set('TASK_COUNT', task_count)
    settings.set('CHANNEL_SIZE', task_count * 3)
    settings.update(spider.custom_settings)
    async with Engine(spider()) as engine:
        await engine.run()
