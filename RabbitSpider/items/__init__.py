from typing import Dict
from collections import defaultdict


class ItemMeta(type):
    def __new__(mcs, name, bases, attrs):
        field: Dict[str, dict] = defaultdict(dict)
        for key, value in attrs.items():
            if not (callable(value) or key.startswith('_')):
                field[key]['value'] = value
            if key == '__annotations__':
                for k, v in value.items():
                    field[k]['annotation'] = v
        cls_instance = super().__new__(mcs, name, bases, attrs)
        cls_instance.FIELDS = field
        return cls_instance
