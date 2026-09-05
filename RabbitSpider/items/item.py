from RabbitSpider.items import ItemMeta
from collections.abc import Iterator, MutableMapping
from typing import Any, ClassVar


class BaseItem(MutableMapping[str, Any], metaclass=ItemMeta):
    FIELDS: ClassVar[dict[str, dict[str, Any]]]

    def __init__(self) -> None:
        self._values: dict[str, Any] = {}
        for k, v in self.FIELDS.items():
            if v.get('value') or v.get('value') == 0:
                self._values[k] = v['value']

    def __setitem__(self, key: str, value: Any) -> None:
        if key in self.FIELDS:
            annotation = self.FIELDS[key].get('annotation')
            if annotation:
                if isinstance(value, annotation):
                    self._values[key] = value
                else:
                    raise TypeError(f"{value} is not type {annotation}")
            else:
                self._values[key] = value
        else:
            raise KeyError(f'field {key} undefined')

    def __getitem__(self, item: str) -> Any:
        return self._values[item]

    def __contains__(self, item: object) -> bool:
        if item in self._values:
            return True
        else:
            return False

    def __iter__(self) -> Iterator[str]:
        return iter(self._values)

    def __len__(self) -> int:
        return len(self._values)

    def __delitem__(self, v: str) -> None:
        del self._values[v]

    def __setattr__(self, key: str, value: Any) -> None:
        if not key.startswith('_'):
            raise
        else:
            super().__setattr__(key, value)

    def __getattribute__(self, item: str) -> Any:
        return super(BaseItem, self).__getattribute__(item)

    def to_dict(self) -> dict[str, Any]:
        return self._values
