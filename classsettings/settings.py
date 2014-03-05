import inspect
import importlib
import functools
import os
from operator import itemgetter

from django.core.exceptions import ImproperlyConfigured

from .utils import defaultargs


@defaultargs
def settings(to_dict=False):
    """
    Adds ability to define Django settings with classes.

    With `to_dict` mode on, calls each public method of decorated class and
    returns dictionary of it's results.
    With `to_dict` mode off, calls each public method of decorated class and
    injects it's values into it's module scope.
    """
    def _convert_to_property(Class):
        for name, method in _get_attributes(Class):
            setattr(Class, name, property(method))

    def _get_attributes(ClassInstance):
        members = sorted(inspect.getmembers(ClassInstance, inspect.ismethod),
                         key=itemgetter(0))
        return filter(lambda (name, member): not name.startswith('_'), members)

    def attrs_injector(Class):
        Class._instance = instance = Class()
        module = importlib.import_module(Class.__module__)
        for name, value in _get_attributes(instance):
            setattr(module, name, value())
        return Class

    def dict_maker(Class):
        Class._instance = instance = Class()
        result = dict(_get_attributes(instance))
        for key in result: result[key] = result[key]()
        return result

    return dict_maker if to_dict else attrs_injector


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

