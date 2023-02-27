__author__ = "calvin"

from typing import Any

from . import Property


class LimitProperty(Property):
    def __init__(self, default_value: Any, min: Any, max: Any):
        super().__init__(default_value, min=min, max=max)

    def __get__(self, obj: Any, objtype: Any = None) -> Any:
        return obj.event_dispatcher_properties[self.name]['value']

    def __set__(self, obj: Any, value: Any) -> None:
        info = obj.event_dispatcher_properties[self.name]
        if value != info['value']:
            # Clip the value to be within min/max
            if value < info['min']:
                # Only dispatch if the current value
                # is not already clipped to the minimum
                if info['value'] != info['min']:
                    info['value'] = info['min']
                else:
                    return
            elif value > info['max']:
                # Only dispatch if the current value
                # is not already clipped to the maximum
                if info['value'] != info['max']:
                    info['value'] = value = info['max']
                else:
                    return
            else:
                info['value'] = value
            # Dispatch callbacks
            for callback in info['callbacks']:
                if callback(obj, value):
                    break

    def __delete__(self, obj: Any) -> None:
        raise AttributeError("Cannot delete properties")

    @staticmethod
    def get_min(inst: Any, name: str) -> Any:
        return inst.event_dispatcher_properties[name]['min']

    @staticmethod
    def set_min(inst: Any, name: str, new_min: Any) -> None:
        inst.event_dispatcher_properties[name]['min'] = new_min
        if getattr(inst, name) < new_min:
            setattr(inst, name, new_min)

    @staticmethod
    def get_max(inst: Any, name: str) -> Any:
        return inst.event_dispatcher_properties[name]['max']

    @staticmethod
    def set_max(inst: Any, name: str, new_max: Any) -> None:
        inst.event_dispatcher_properties[name]['max'] = new_max
        if getattr(inst, name) > new_max:
            setattr(inst, name, new_max)
