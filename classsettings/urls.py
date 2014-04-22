import inspect
import itertools
import traceback

from django.core import urlresolvers
from django.core.exceptions import ImproperlyConfigured
from django.conf.urls import url as django_url
from django.utils import six


class Scope(object):

    __CURRENT = None

    @classmethod
    def get_current(cls):
        return cls.__CURRENT

    @classmethod
    def _set_current(cls, scope):
        if cls.__CURRENT:
            cls.__CURRENT._add_child(scope)

        cls.__CURRENT = scope

    @classmethod
    def _close_current(cls):
        cls.__CURRENT = cls.__CURRENT.parent

    def __init__(self, regex=None, view=None, name=None, **context_variables):
        self._regex = regex
        self._view = view
        self._name = name
        self._own_context = context_variables
        self._parent = None
        self.childs = []

    def __enter__(self):
        Scope._set_current(self)
        return self

    def __exit__(self, exc_type, exc_value, tb):
        Scope._close_current()

        if exc_value:
            raise exc_value

    def __getitem__(self, key):
        if key in self._own_context:
            return self._own_context[key]
        elif self.parent:
            return self.parent[key]
        
        raise KeyError(key)

    def __setitem__(self, key, value):
        self._own_context[key] = value

    def _add_child(self, scope_or_url):
        self.childs.append(scope_or_url)

        if isinstance(scope_or_url, type(self)):
            scope_or_url._parent = self

    def _del_child(self, scope_or_url):
        self.childs.remove(scope_or_url)

        if isinstance(scope_or_url, type(self)):
            scope_or_url._parent = None

    def _format_string(self, value, base):
        args = () if base is None else (base,)
        
        try:
            return value.format(*args, **self.context)
        except (IndexError, KeyError) as e:
            raise ImproperlyConfigured({
                IndexError: 'Could not format "%s", base value is None' % value,
                KeyError: '"%s" context variable not found' % e.args[0]
            }[type(e)])

    def _resolve(self, regex, view, kwargs, name, prefix):
        url_scope = Scope(regex, view, name)
        self._add_child(url_scope)
        args = url_scope.regex, url_scope.view, kwargs, url_scope.name, prefix
        self._del_child(url_scope); del url_scope
        return args

    @property
    def context(self):
        result, scope = {}, self
        while scope:
            for key, value  in scope._own_context.iteritems():
                result.setdefault(key, value)

            scope = scope.parent
        return result

    @property
    def parent(self):
        return self._parent

    @property
    def regex(self):
        if self.parent:
            if self._regex is None:
                return self.parent.regex
            else:
                return self._format_string(self._regex, self.parent.regex)
        else:
            if self._regex is None:
                return None
            else:
                return self._format_string(self._regex, None)

    @property
    def view(self):
        view = self._view

        if self.parent:
            if isinstance(self.parent.view, six.string_types):
                if isinstance(self._view, six.string_types):
                    view_path = self._format_string(self._view, self.parent.view)
                    view = urlresolvers.get_callable(view_path)
                else:
                    view = urlresolvers.get_callable(self._view)
            elif inspect.ismodule(self.parent.view):
                if isinstance(self._view, six.string_types):
                    view = getattr(self.parent.view, self._view)

        if inspect.isfunction(getattr(view, 'as_view', None)):
            view = view.as_view()

        return view

    @property
    def name(self):
        if self.parent:
            if self._name is None:
                return self.parent.name
            else:
                return self._format_string(self._name, self.parent.name)
        else:
            if self._name is None:
                return None
            else:
                return self._format_string(self._name, None)
    
    def _urls_generator(self):
        for child in self.childs:
            if isinstance(child, type(self)):
                for url_obj in child.urls:
                    yield url_obj
            else:
                yield child

    @property
    def urls(self):
        return tuple(self._urls_generator())

    def url(self, regex, view, kwargs=None, name=None, prefix=''):
        url_args = self._resolve(regex, view, kwargs, name, prefix)
        url_obj = django_url(*url_args)
        self._add_child(url_obj)
        return url_obj    


def url(regex, view, kwargs=None, name=None, prefix=''):
    scope = Scope.get_current()
    url_args = (regex, view, kwargs, name, prefix)
    return scope.url(*url_args) if scope else django_url(*url_args)
