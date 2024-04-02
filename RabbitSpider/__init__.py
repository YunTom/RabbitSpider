from RabbitSpider.utils.control import SettingManager
from RabbitSpider.utils.control import TaskManager
from RabbitSpider.core.download import Download
from RabbitSpider.core.scheduler import Scheduler

setting = SettingManager()
download = Download()

scheduler = Scheduler(setting.get('RABBIT_USERNAME'),
                      setting.get('RABBIT_PASSWORD'),
                      setting.get('RABBIT_HOST'),
                      setting.get('RABBIT_PORT'),
                      setting.get('RABBIT_VIRTUAL_HOST'))

max_retry = setting['MAX_RETRY']
