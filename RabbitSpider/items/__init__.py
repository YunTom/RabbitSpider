from typing import Any
from abc import ABCMeta
from collections import defaultdict


class ItemMeta(ABCMeta):
    def __new__(
            mcs,
            name: str,
            bases: tuple[type, ...],
            attrs: dict[str, Any],
            **kwargs: Any,
    ) -> type:
        field: dict[str, dict[str, Any]] = defaultdict(dict)
        for key, value in attrs.items():
            if not (callable(value) or key.startswith('_')):
                field[key]['value'] = value
            if key == '__annotations__':
                for k, v in value.items():
                    field[k]['annotation'] = v
        cls_instance = super().__new__(mcs, name, bases, attrs, **kwargs)
        cls_instance.FIELDS = field
        return cls_instance
