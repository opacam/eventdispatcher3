from __future__ import annotations
import json as JSON
from future.utils import iteritems, iterkeys, itervalues
from builtins import int, str
from typing import Dict, List, Union, Any
from . import (
    DictProperty,
    ListProperty,
    Property,
    StringProperty,
    EventDispatcher,
    ObservableDict,
    ObservableList,
)
from collections import OrderedDict
from functools import partial
from itertools import chain
import numpy as np

eventdispatcher_map: Dict[
    Union[type, None],
    Union[type[DictProperty], type[ListProperty], type[Property]],
] = {
    dict: DictProperty,    OrderedDict: DictProperty,
    list: ListProperty,    np.ndarray: ListProperty,
    tuple: Property,       int: Property,
    float: Property,       str: StringProperty,
    bool: Property,        None: Property,
}

eventdispatcher_map.update(
    {
        t: Property
        for t in (
            np.int8, np.int16, np.int32, np.int64,
            np.uint8, np.uint16, np.uint32, np.uint64,
            np.float16, np.float32, np.float64,
        )
    }
)


class NoAttribute(object):
    pass


class JSON_Map(EventDispatcher):
    def __init__(self, json: dict[str, Any]) -> None:
        self.raw: dict[str, Any] = json
        super().__init__(json)

        cls = self.__class__

        # Map the json structure to event dispatcher properties
        # but only those attributes which do not already exist in the object
        properties = JSON_Map.map_attributes(self, json)

        self._python_properties: set[str] = set()
        for c in cls.__mro__:
            for attr_name, attr in iteritems(c.__dict__):
                if isinstance(attr, property):
                    self._python_properties.add(attr_name)

        self._json_maps: Dict[str, JSON_Map] = {}
        for attr_name, attr in iteritems(self.__dict__):
            if isinstance(attr, JSON_Map) and attr_name in json:
                self._json_maps[attr_name] = attr

        with self.temp_unbind_all(*iterkeys(self.event_dispatcher_properties)):
            for key in iterkeys(properties):
                if key in json:
                    setattr(self, key, json[key])
        self.bind(**{p: partial(self._update_raw, p) for p in properties})

    def keys(self) -> List[str]:
        return [v for v in iterkeys(self)]

    def values(self) -> List[Any]:
        return [v for v in itervalues(self)]

    def items(self) -> List[tuple[str, Any]]:
        return [v for v in iteritems(self)]

    def get(self, *args) -> Any:
        try:
            return getattr(self, *args)
        except KeyError:
            if len(args) == 2:
                return args[1]
            else:
                return None

    def iteritems(self) -> Any:
        for key in self.iterkeys():
            yield key, getattr(self, key)

    def iterkeys(self) -> Any:
        return chain(
            iterkeys(self.event_dispatcher_properties),
            self._python_properties,
            iterkeys(self._json_maps),
        )

    def itervalues(self) -> Any:
        for key in self.iterkeys():
            yield getattr(self, key)

    def __reduce__(self) -> tuple[type, tuple, None, None, Any]:
        return dict, tuple(), None, None, self.iteritems()

    def __contains__(self, item: str) -> bool:
        return item in self.event_dispatcher_properties or isinstance(
            getattr(self.__class__, item, AttributeError), property
        )

    def __getitem__(self, item: str) -> Any:
        value = getattr(self, item, KeyError)
        if value is KeyError:
            raise KeyError(item)
        else:
            return value

    def __setitem__(self, key: str, value: Any) -> None:
        if key in self.event_dispatcher_properties or isinstance(
            getattr(self.__class__, key, AttributeError), property
        ):
            # The key maps to an event dispatcher property or python property
            setattr(self, key, value)
        else:
            raise TypeError("Cannot set %s using item assignment" % key)

    def to_dict(self) -> Dict[str, Any]:
        """
        Creates a dictionary representation of the JSON_Map that includes it's
        @property values and all sub-JSON_Maps.
        """
        d = {}
        for k, v in self.iteritems():
            if isinstance(v, JSON_Map):
                d[k] = v.to_dict()
            elif isinstance(v, ObservableDict):
                d[k] = dict(v)
            elif isinstance(v, ObservableList):
                d[k] = list(v)
            else:
                d[k] = v
        return d

    def update(self, E=None, **F) -> None:
        if E and self.raw != E:
            for k, v in E.items():
                if hasattr(self[k], "update"):
                    self[k].update(v)
                else:
                    self[k] = v
        elif F and self.raw != F:
            for k, v in F.items():
                if hasattr(self[k], "update"):
                    self[k].update(v)
                else:
                    self[k] = v

    def _update_raw(self, property_name: str, inst: Any, value: Any) -> None:
        """
        Callback to keep property values in sync with the underlying JSON
        object.
        """
        if property_name in self.raw:
            self.raw[property_name] = value
        else:
            raise AttributeError(
                "Attribute %s is not found in the underlying JSON object."
                % property_name
            )

    @staticmethod
    def map_attributes(obj: Any, json: Dict[str, Any]) -> Dict[str, Any]:
        """
        Iterate through the JSON structure and create EventDispatcher
        properties for the attributes.
        """
        cls = obj.__class__
        unregistered: Dict[str, Any] = {}
        properties: Dict[str, Any] = {}
        for attr, value in json.iteritems():
            if hasattr(obj, attr):
                if attr in obj.event_dispatcher_properties:
                    properties[attr] = obj.event_dispatcher_properties[attr]
                continue
            elif any(
                [
                    isinstance(getattr(c, attr, NoAttribute), property)
                    for c in cls.__mro__
                ]
            ):
                # Check if any class attributes are properties
                continue
            else:
                properties[attr] = unregistered[attr] = eventdispatcher_map[
                    type(value)
                ](value)
                setattr(cls, attr, properties[attr])
        if unregistered:
            EventDispatcher.register_properties(obj, unregistered)
        return properties


if __name__ == "__main__":
    path = input("Please enter path to Json file: ")
    print("The target json file is {path}")
    with open(path, "r") as f:
        js = JSON.load(f)
    obj = JSON_Map.map("PlatformConfig", js)
