from collections.abc import MutableMapping
from RabbitSpider.items import ItemMeta


class BaseItem(MutableMapping, metaclass=ItemMeta):
    FIELDS: dict = {}

    def __init__(self):
        self._values = {}

    def __setitem__(self, key, value):
        if key in self.FIELDS:
            self._values[key] = value
        else:
            raise KeyError(f'field {key} undefined')

    def __getitem__(self, item):
        return self._values[item]

    def __iter__(self):
        return iter(self._values)

    def __len__(self) -> int:
        return len(self._values)

    def __delitem__(self, v):
        delattr(self._values, v)

    def __setattr__(self, key, value):
        if not key.startswith('_'):
            raise
        else:
            super().__setattr__(key, value)

    def __getattribute__(self, item):
        field = super().__getattribute__('FIELDS')
        if item in field:
            raise
        else:
            return super(BaseItem, self).__getattribute__(item)

    def to_dict(self):
        return dict(self)

