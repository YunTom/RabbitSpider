from RabbitSpider.items import ItemMeta


class BaseItem(metaclass=ItemMeta):
    def __init__(self):
        self._values = {}
        for k, v in self.FIELDS.items():
            if v.get('value'):
                self._values[k] = v['value']

    def __setitem__(self, key, value):
        if key in self.FIELDS:
            if self.FIELDS[key]['annotation']:
                if isinstance(value, self.FIELDS[key]['annotation']):
                    self._values[key] = value
                else:
                    raise TypeError(f"{value} is not type {self.FIELDS[key]['annotation']}")
            else:
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
        return self._values
