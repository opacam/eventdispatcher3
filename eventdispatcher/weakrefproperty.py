__author__ = "calvin"

from copy import deepcopy

from eventdispatcher import Property
from weakref import ref


class WeakRefProperty(Property):
    """
    Property that stores it's values as weak references in order to facilitate
    garbage collection.
    """

    def __init__(self, default_value: any, **additionals: dict) -> None:
        self.instances = {}
        try:
            self.default_value = ref(default_value)
        except TypeError:
            self.default_value = None
        try:
            self.value = ref(deepcopy(default_value))
        except TypeError:
            self.value = None
        self._additionals = additionals

    def __get__(self, obj: any, objtype: type = None) -> any:
        value = obj.event_dispatcher_properties[self.name]["value"]
        if value:
            return value()
        else:
            return value

    def __set__(self, obj: any, value: any) -> None:
        wr = ref(value) if value is not None else None
        if wr != obj.event_dispatcher_properties[self.name]["value"]:
            prop = obj.event_dispatcher_properties[self.name]
            prop["value"] = wr
            for callback in prop["callbacks"]:
                if callback(obj, value):
                    break

    def register(
        self, instance: any, property_name: str, default_value: any
    ) -> None:
        wr = None if default_value is None else ref(default_value)
        super(WeakRefProperty, self).register(instance, property_name, wr)
