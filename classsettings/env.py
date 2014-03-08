import functools
import os

from django.core.exceptions import ImproperlyConfigured

from .utils import defaultargs


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
            except ImproperlyConfigured as e:
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
