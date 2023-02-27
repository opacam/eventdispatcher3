__author__ = 'calvin'

from collections.abc import MutableMapping
from future.utils import iteritems, iterkeys, itervalues
from functools import partial
from typing import Any, Callable, Dict, Optional, Tuple

from . import Property


class __DoesNotExist__:
    # Custom class used as a flag
    pass


class ObservableDict(MutableMapping):
    def __init__(self, dictionary: Dict, dispatch_method: Callable) -> None:
        self.dictionary: Dict = dictionary.copy()
        self.dispatch: Callable = dispatch_method

    def __repr__(self) -> str:
        return self.dictionary.__repr__()

    def __get__(self, instance: Any, owner: Any) -> Dict:
        return self.dictionary

    def __contains__(self, item: Any) -> bool:
        return item in self.dictionary

    def __getitem__(self, item: Any) -> Any:
        return self.dictionary[item]

    def __setitem__(self, key: Any, value: Any) -> None:
        prev = self.dictionary.get(key, __DoesNotExist__)
        self.dictionary[key] = value
        try:
            # Ensure that the comparison evaluates as a
            # scalar boolean (unlike numpy arrays)
            dispatch = bool(prev != value)
        except Exception:
            dispatch = True
        if dispatch:
            self.dispatch(self.dictionary)

    def clear(self) -> None:
        if len(self.dictionary):
            self.dictionary.clear()
            self.dispatch(self.dictionary)

    def __len__(self) -> int:
        return len(self.dictionary)

    def __eq__(self, other: Any) -> bool:
        return self.dictionary == other

    def __cmp__(self, other: Any) -> bool:
        return self.dictionary == other

    def __ne__(self, other: Any) -> bool:
        return self.dictionary != other

    def __delitem__(self, key: Any) -> None:
        del self.dictionary[key]
        self.dispatch(self.dictionary)

    def __iter__(self) -> Any:
        return iter(self.dictionary)

    def __nonzero__(self) -> bool:
        return bool(self.dictionary)

    def __getstate__(self) -> Dict:
        return self.dictionary

    def __reduce__(self) -> Tuple:
        return dict, tuple(), None, None, iter(iteritems(self.dictionary))

    def copy(self) -> Dict:
        return self.dictionary.copy()

    def get(self, key: Any, default: Optional[Any] = None) -> Any:
        return self.dictionary.get(key, default)

    def itervalues(self) -> Any:
        return itervalues(self.dictionary)

    def iterkeys(self) -> Any:
        return iterkeys(self.dictionary)

    def iteritems(self) -> Any:
        return iteritems(self.dictionary)

    def update(self, _dict: Optional[Dict] = None, **kwargs: Any) -> None:
        if _dict:
            try:
                not_equal = bool(self.dictionary != _dict)
            except Exception:
                not_equal = True
            if not_equal:
                self.dictionary.update(_dict)
                self.dispatch(self.dictionary)
        elif kwargs:
            try:
                not_equal = bool(self.dictionary != kwargs)
            except Exception:
                not_equal = True
            if not_equal:
                self.dictionary.update(kwargs)
                self.dispatch(self.dictionary)

    def keys(self) -> Any:
        return self.dictionary.keys()

    def values(self) -> Any:
        return self.dictionary.values()

    def items(self) -> Any:
        return self.dictionary.items()

    def pop(self, key: Any) -> Any:
        item = self.dictionary.pop(key)
        self.dispatch(self.dictionary)
        return item


class DictProperty(Property):
    def __init__(self, default_value: Dict, **kwargs: Any) -> None:
        super().__init__(default_value, **kwargs)
        if not isinstance(default_value, dict):
            raise ValueError('DictProperty takes dict only.')

    def register(self, instance: Any, property_name: str, value: Dict) -> None:
        self.value = ObservableDict(
            value,
            dispatch_method=partial(
                instance.dispatch, property_name, instance
            ),
        )
        super().register(instance, property_name, self.value)

    def __set__(self, obj: Any, value: Dict) -> None:
        p = self.instances[obj]
        try:
            # Ensure that the comparison evaluates as a
            # scalar boolean (unlike numpy arrrays)
            do_dispatch = bool(p['value'] != value)
        except Exception:
            do_dispatch = True
        if do_dispatch:
            p['value'].dictionary.clear()
            # Assign to the ObservableDict's value
            p['value'].dictionary.update(value)
            for callback in p['callbacks']:
                if callback(obj, value):
                    break
