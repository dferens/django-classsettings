import inspect
import importlib
from operator import itemgetter


__all__ = ('Settings', 'Config')


def inspect_class(cls):
    cls._instance = instance = cls()
    module = importlib.import_module(cls.__module__)
    members = sorted(inspect.getmembers(instance, inspect.ismethod),
                     key=itemgetter(0))
    public_members = [m for m in members if not m[0].startswith('_')]
    return public_members, module


class SettingsMeta(type):

    def __init__(cls, *args):
        public_members, module = inspect_class(cls)
        for member_name, member in public_members:
            setattr(module, member_name, member())


class ConfigMeta(type):

    def __init__(cls, cls_name, base_classes, params):
        public_members, module = inspect_class(cls)
        result_config = dict((name, value()) for (name, value) in public_members)
        setattr(module, cls_name, result_config)


class Settings(object):
    """
    Calls each public method of class and injects it's value into it's module scope.
    """
    __metaclass__ = SettingsMeta


class Config(object):
    """
    Calls each public method of class, constructs dictionary with `name-result`
    pairs and injects it into module scope.
    """
    __metaclass__ = ConfigMeta
