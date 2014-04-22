import inspect
import itertools
import traceback

from django.core import urlresolvers
from django.core.exceptions import ImproperlyConfigured
from django.conf.urls import url as django_url
from django.utils import six


class Context(object):
    """
    Dict-like object, can contain reference to parent context.

    Keys seek order: own keys, parent context and raises KeyError if not found.
    """
    def __init__(self, parent=None, **variables):
        self._parent = parent
        self._own_context = variables

    def __iter__(self):
        return self._own_context.__iter__()

    def __getitem__(self, key):
        context = self
        while context:
            if key in context._own_context:
                return context._own_context[key]

            context = context.parent
        raise KeyError(key)

    def __setitem__(self, key, value):
        self._own_context[key] = value

    def __str__(self):
        items = ', '.join("'%s': %s" % (k, self[k]) for k in self.keys())
        return '<Context object {%s}>' % items

    def __repr__(self):
        return self.__str__()

    def dict(self):
        result, context = dict(), self
        while context:
            for k in context:
                result.setdefault(k, context[k])

            context = context.parent
        return result

    def keys(self):
        result, context = list(), self
        while context:
            result.extend(k for k in context if k not in result)
            context = context.parent
        return result

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, value):
        if value is None or isinstance(value, type(self)):
            self._parent = value
        else:
            raise TypeError('Value "%s" is not "%s" instance' %
                            (value, type(self).__name__))


class Scope(object):
    """
    Allows urls defined with :func:`classsettings.urls.url` within scope use
    it's variables for string substitutions with `{var_name}` and attribute
    lookups for modules.
    """

    # Globally accessed object, not threadsafe at all
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
        self._own_context = Context(None, **context_variables)
        self.parent = None
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
            scope_or_url.parent = self

    def _del_child(self, scope_or_url):
        self.childs.remove(scope_or_url)

        if isinstance(scope_or_url, type(self)):
            scope_or_url.parent = None

    def _format_string(self, value, base):
        args = () if base is None else (base,)
        
        try:
            return value.format(*args, **(self.context.dict()))
        except (IndexError, KeyError, ValueError) as e:
            if type(e) is IndexError:
                msg = 'Could not format "%s", base value is None' % value
            elif type(e) is KeyError:
                msg = '"%s" context variable not found' % e.args[0]
            elif type(e) is ValueError and e.args[0] == 'zero length field name in format':
                msg = 'Positional argument specifiers ("{}") can be omitted ' \
                      'on >=2.7 only, use "{0}" instead.'
            else:
                msg = None
            
            raise (ImproperlyConfigured(msg) if msg else e)

    def _resolve(self, regex, view, kwargs, name, prefix):
        url_scope = Scope(regex, view, name)
        self._add_child(url_scope)
        args = url_scope.regex, url_scope.view, kwargs, url_scope.name, prefix
        self._del_child(url_scope); del url_scope
        return args

    @property
    def context(self):
        return self._own_context

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, scope):
        self._parent = scope
        self._own_context.parent = scope._own_context if scope else None

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
            if view is None:
                view = self.parent.view
            else:
                if isinstance(self.parent.view, six.string_types):
                    if isinstance(self._view, six.string_types):
                        view_path = self._format_string(self._view, self.parent.view)
                        view = urlresolvers.get_callable(view_path)
                    else:
                        view = urlresolvers.get_callable(self._view)
                elif inspect.ismodule(self.parent.view):
                    if isinstance(self._view, six.string_types):
                        view = getattr(self.parent.view, self._view)

        as_view = getattr(view, 'as_view', None)
        view = as_view() if callable(as_view) else view

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
        """
        Modifies url's url pattern view and name only.
        """
        url_args = self._resolve(regex, view, kwargs, name, prefix)
        url_obj = django_url(*url_args)
        self._add_child(url_obj)
        return url_obj    


def url(regex, view, kwargs=None, name=None, prefix=''):
    """
    Shortcut for ``url`` method of current scope.

    Acts like native django's ``url`` if is defined outside scope.
    """
    scope = Scope.get_current()
    url_args = (regex, view, kwargs, name, prefix)
    return scope.url(*url_args) if scope else django_url(*url_args)
