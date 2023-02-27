from __future__ import annotations
__author__ = "calvin"

from collections.abc import MutableSet
from functools import partial
from . import Property


class ObservableSet(MutableSet):
    def __init__(self, dictionary: dict, dispatch_method):
        self.set: set = dictionary.copy()
        self.dispatch = dispatch_method

    def __repr__(self) -> str:
        return self.set.__repr__()

    def __get__(self, instance, owner) -> set:
        return self.set

    def __contains__(self, item) -> bool:
        return item in self.set

    def __len__(self) -> int:
        return len(self.set)

    def __getitem__(self, item) -> object:
        return self.set[item]

    def __setitem__(self, key, value):
        try:
            prev = self.set[key]
            check = prev != value
        except KeyError:
            check = True
        self.set[key] = value
        if check:
            self.dispatch(self.set)

    def __eq__(self, other) -> bool:
        # Must be this order and not self.set == other,
        # otherwise unittest.assertEquals fails
        return other == self.set

    def __cmp__(self, other) -> bool:
        return self.set == other

    def __ne__(self, other) -> bool:
        return self.set != other

    def __delitem__(self, key):
        del self.set[key]
        self.dispatch(self.set)

    def __iter__(self) -> iter:
        return iter(self.set)

    def __nonzero__(self) -> bool:
        return bool(self.set)

    def __getstate__(self) -> set:
        return self.set

    def __reduce__(self) -> tuple:
        return (set, (tuple(self.set),), None, None, None)

    def add(self, value):
        self.set.add(value)

    def discard(self, value):
        self.set.discard(value)

    def copy(self) -> "ObservableSet":
        return self.__class__(self.set, self.dispatch)

    def get(self, key, default=None) -> object:
        self.set.get(key, default)

    def remove(self, item):
        self.set.remove(item)
        self.dispatch(self.set)

    def update(self, *items):
        if self.set != items:
            self.set.update(*items)
            self.dispatch(self.set)

    def pop(self) -> object:
        item = self.set.pop()
        self.dispatch(self.set)
        return item

    def difference(self, items) -> set:
        return self.set.difference(items)


class SetProperty(Property):
    def __init__(self, default_value: set, **kwargs):
        super().__init__(default_value, **kwargs)
        if not isinstance(default_value, set):
            raise ValueError("SetProperty takes sets only.")

    def register(self, instance, property_name: str, value: set):
        self.value = ObservableSet(
            value,
            dispatch_method=partial(
                instance.dispatch, property_name, instance
            ),
        )
        super().register(instance, property_name, self.value)

    def __set__(self, obj, value: set):
        p = self.instances[obj]
        do_dispatch = p["value"] != value
        p["value"].set.clear()
        p["value"].set.update(value)  # Assign to the ObservableDict's value
        if do_dispatch:
            for callback in p["callbacks"]:
                if callback(obj, value):
                    break
