__author__ = "calvin"

from collections.abc import MutableSequence
from functools import partial
from copy import copy
from typing import List, Tuple, Union
import numpy as np

from . import Property


class ObservableList(MutableSequence):
    def __init__(
        self,
        target_list: Union[List, Tuple],
        dispatch_method: callable,
        dtype: type = None,
    ) -> None:
        if (
            not isinstance(target_list, (list, tuple, ObservableList))
        ):
            raise ValueError(
                "Observable list must only be initialized "
                "with sequences as arguments"
            )
        if dtype:
            self.list = np.array(target_list, dtype=dtype)
        else:
            self.list = list(target_list)

        self.dispatch = dispatch_method

    def __repr__(self) -> str:
        return self.list.__repr__()

    def __get__(self, instance: object, owner: type) -> list:
        return self.list

    def __getitem__(self, item: int) -> any:
        return self.list[item]

    def __setitem__(self, key: int, value: any) -> None:
        try:
            not_equal = bool(self.list[key] != value)
        except Exception:
            not_equal = True
        if not_equal:
            self.list[key] = value
            self.dispatch(self.list)

    def __reversed__(self) -> iter:
        return reversed(self.list)

    def __delitem__(self, key: int) -> None:
        del self.list[key]
        self.dispatch(self.list)

    def __len__(self) -> int:
        return len(self.list)

    def __iter__(self) -> iter:
        return iter(self.list)

    def __nonzero__(self) -> bool:
        return bool(self.list)

    def __getstate__(self) -> list:
        return self.list

    def __reduce__(self) -> tuple:
        return (list, tuple(), None, iter(self.list), None)

    def insert(self, index: int, value: any) -> None:
        self.list.insert(index, value)
        self.dispatch(self.list)

    def append(self, value: any) -> None:
        self.list.append(value)
        self.dispatch(self.list)

    def extend(self, values: list) -> None:
        self.list.extend(values)
        self.dispatch(self.list)

    def pop(self, index: int = -1) -> any:
        value = self.list.pop(index)
        self.dispatch(self.list)
        return value

    def copy(self) -> list:
        return copy(self.list)

    def __eq__(self, other: list) -> bool:
        return self.list == other

    def __ne__(self, other: list) -> bool:
        return self.list != other


class ListProperty(Property):
    def register(
        self,
        instance: object,
        property_name: str,
        value: list,
        dtype: type = None,
    ) -> None:
        self.value = ObservableList(
            value,
            dispatch_method=partial(
                instance.dispatch, property_name, instance
            ),
            dtype=self._additionals.get("dtype"),
        )
        super(ListProperty, self).register(instance, property_name, self.value)

    def __set__(self, obj: object, value: list) -> None:
        p = self.instances[obj]
        # Check if we need to dispatch
        do_dispatch = len(p["value"].list) != len(
            value
        ) or not ListProperty.compare_sequences(p["value"], value)
        # do_dispatch = not ListProperty.compare_sequences(p['value'], value)
        p["value"].list[:] = value  # Assign to ObservableList's value
        if do_dispatch:
            for callback in p["callbacks"]:
                if callback(obj, p["value"].list):
                    break

    @staticmethod
    def compare_sequences(iter1: list, iter2: list) -> bool:
        """
        Compares two iterators to determine if they are equal.
        Used to compare lists and tuples.
        """
        try:
            for a, b in zip(iter1, iter2):
                if a != b:
                    return False
        except Exception:
            # A ValueError is usually raised if comparing numpy arrays because
            # they return an array of booleans rather than a scalar value.
            # If any error occurs during comparison just assume they are not
            # equal.
            return False
        return True
