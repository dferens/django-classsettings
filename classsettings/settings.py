import inspect
import sys
from operator import itemgetter

from django.utils import six, importlib


def inspect_class(cls):
    cls._instance = instance = cls()
    module = importlib.import_module(cls.__module__)
    members = sorted(inspect.getmembers(instance, inspect.ismethod),
                     key=itemgetter(0))
    public_members = [m for m in members if not m[0].startswith('_')]
    return public_members, module


class SettingsMeta(type):

    def __init__(cls, name, bases, attrs):
        public_members, module = inspect_class(cls)
        for member_name, member in public_members:
            setattr(module, member_name, member())


class ConfigMeta(type):

    def __new__(cls, name, bases, attrs):
        Class = super(ConfigMeta, cls).__new__(cls, name, bases, attrs)

        if name == 'NewBase':
            return Class

        public_members, module = inspect_class(Class)
        variables = ((k, val()) for (k, val) in public_members)
        result = ConfigResult(variables, Class)
        setattr(module, name, result)
        return result


class ConfigResult(dict):
    """
    Dict-like object which adds inheritance support.
    """
    def __new__(cls, *args, **kwargs):
        if len(args) == 2:
            # Used to create dict object
            return super(ConfigResult, cls).__new__(cls, *args, **kwargs)
        else:
            # Used as superclass
            name, bases, attrs = args
            bases = tuple(b.ConfigClass for b in bases if isinstance(b, ConfigResult))
            return ConfigMeta(name, bases, attrs)

    def __init__(self, *args, **kwargs):
        if len(args) == 2:
            # Is used as dict instance
            dict_arg, self._ConfigClass = args
            super(ConfigResult, self).__init__(dict_arg, **kwargs)
        else:
            # Is used as class
            pass

    @property
    def ConfigClass(self):
        return self._ConfigClass


class Settings(six.with_metaclass(SettingsMeta)):
    """
    Calls each public method of class and injects it's value into it's
    module's scope.
    """


class Config(six.with_metaclass(ConfigMeta)):
    """
    Calls each public method of class, constructs dictionary with `name-result`
    pairs and replaces class with it.
    """
