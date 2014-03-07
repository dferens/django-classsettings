import inspect
import importlib
from itertools import izip
import functools
import os
from operator import itemgetter

from django.core.exceptions import ImproperlyConfigured

from .utils import defaultargs


def inspect_class(cls):
    cls._instance = instance = cls()
    module = importlib.import_module(cls.__module__)
    members = sorted(inspect.getmembers(instance, inspect.ismethod),
                     key=itemgetter(0))
    public_members = [m for m in members if not m[0].startswith('_')]
    return public_members, module


class SettingsMeta(type):
    """
    Calls each public method of class and injects it's value into it's module scope.
    """
    def __init__(cls, *args):
        public_members, module = inspect_class(cls)
        for member_name, member in public_members:
            setattr(module, member_name, member())


class ConfigMeta(type):
    """
    Calls each public method of class, constructs dictionary with `name-result`
    pairs and injects it into module scope.
    """
    def __init__(cls, cls_name, base_classes, params):
        public_members, module = inspect_class(cls)
        result_config = dict((name, value()) for (name, value) in public_members)
        setattr(module, cls_name, result_config)


class Settings(object):

    __metaclass__ = SettingsMeta


class Config(object):
    __metaclass__ = ConfigMeta


@defaultargs
def from_env(key=None):
    """
    Gets environment variable by given key.
    If key is not given, uses decorated function's name.
    If key is not present within environ, calls given function and raises
    :class:`ImproperlyConfigured` if it returns `None`.
    """
    def decorator(func):
        @functools.wraps(func)
        def decorated(*args, **kwargs):
            try:
                return get_env_setting(key or func.__name__)
            except ImproperlyConfigured, e:
                default = func(*args, **kwargs)
                if default is not None: return default
                raise e

        return decorated
    return decorator


def get_env_setting(setting):
    """
    Gets the environment setting and raises exception if it isn't present.
    """
    try:
        return os.environ[setting]
    except KeyError:
        error_msg = "Set the %s env variable" % setting
        raise ImproperlyConfigured(error_msg)

