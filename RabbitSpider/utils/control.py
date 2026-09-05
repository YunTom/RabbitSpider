from importlib import import_module
from RabbitSpider import default_settings


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
