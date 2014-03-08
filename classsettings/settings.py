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

    def __init__(cls, name, bases, attrs):
        public_members, module = inspect_class(cls)
        result = dict((name, value()) for (name, value) in public_members)
        setattr(module, name, result)


class Settings(six.with_metaclass(SettingsMeta)):
    """
    Calls each public method of class and injects it's value into it's
    module's scope.
    """


class Config(six.with_metaclass(ConfigMeta)):
    """
    Calls each public method of class, constructs dictionary with `name-result`
    pairs and injects it into module scope.
    """
