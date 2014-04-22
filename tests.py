import os
import sys
import unittest

import mock
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.unittest import skipIf

from classsettings import Settings, Config, from_env, utils
from classsettings.urls import Context, Scope, url


IS_ABOVE_26 = sys.version_info[0] > 2 or sys.version_info[1] > 6

settings.configure()


class InjectorTestCase(unittest.TestCase):

    def setUp(self):
        self._old_globals = dict(globals())

    def tearDown(self):
        for k in  [k for k in globals() if k not in self._old_globals]:
            globals().pop(k)


class SettingsTestCase(InjectorTestCase):

    def test_fields(self):
        old_module_vars = set(globals())
        self.assertFalse('public_method' in old_module_vars)

        class MySettings(Settings):
            def public_method(self): return 1
            def _private_method(self): return 2
            some_field = 2
            class some_class(object): pass

        new_module_vars = set(globals())
        self.assertEqual(new_module_vars - old_module_vars,
                         set(('public_method', 'some_field', 'some_class')))

    def test_related(self):
        class MySettings(Settings):
          def _private_setting(self): return 1
          def public_setting(self): return self._private_setting() * 2

        self.assertEqual(globals()['public_setting'], 2)

    def test_inheritance(self):
        old_module_vars = set(globals())
        self.assertFalse('public_super' in old_module_vars or
                         'public_sub' in old_module_vars)

        class SuperSettings(Settings):
            def public_super(self): return 1

        class SubSettings(SuperSettings):
            def public_sub(self): return 2

        self.assertEqual(set(globals()) - old_module_vars,
                         set(('public_sub', 'public_super')))
        self.assertEqual(globals()['public_super'], 1)
        self.assertEqual(globals()['public_sub'], 2)


class ConfigTestCase(InjectorTestCase):

    def test_injects(self):
        old_module_vars = set(globals())
        self.assertFalse('MyConfig' in old_module_vars)

        class MyConfig(Config): pass

        new_module_vars = set(globals())
        self.assertEqual(new_module_vars - old_module_vars,
                         set(('MyConfig',)))
        self.assertTrue(globals()['MyConfig'] == MyConfig == dict())

    def test_fields(self):
        class MyConfig(Config):
           def public_method(self): return 1
           def _private_method(self): return 2
           some_field = 2
           class some_class(object): pass

        result_dict = globals()['MyConfig']
        self.assertEqual(result_dict, {'public_method': 1, 'some_field': 2,
                                       'some_class': MyConfig['some_class']})

    def test_related(self):
        class MyConfig(Config):
           def public_setting(self): return self._private_setting() * 2
           def _private_setting(self): return 1

        self.assertEqual(globals()['MyConfig'], {'public_setting': 2})

    def test_inheritance(self):
        old_module_vars = set(globals())
        self.assertFalse('SuperConfig' in old_module_vars or
                         'Sub1Config' in old_module_vars)

        class SuperConfig(Config):
            def public_super(self): return 1

        class Sub1Config(SuperConfig):
            def public_sub(self): return 2 * self.public_super()

        class Sub2Config(Sub1Config):
            def public_sub2(self): return 2 * self.public_sub()

        self.assertEqual(set(globals()) - old_module_vars,
                         set(('SuperConfig', 'Sub1Config', 'Sub2Config')))
        self.assertEqual(SuperConfig, dict(public_super=1))
        self.assertEqual(Sub1Config,  dict(public_super=1, public_sub=2))
        self.assertEqual(Sub2Config,  dict(public_super=1, public_sub=2, public_sub2=4))


class FromEnvTestCase(unittest.TestCase):

    def setUp(self):
        self._old_environ = dict(os.environ)

    def tearDown(self):
        for key in [k for k in os.environ if k not in self._old_environ]:
            os.environ.pop(key)

    def test_has_default(self):
        self.assertEqual(os.environ.get('CLASSSETTINGS_ENV'), None)

        @from_env(key='CLASSSETTINGS_ENV')
        def getter(): return 'default'

        self.assertEqual(getter(), 'default')
        os.environ['CLASSSETTINGS_ENV'] = 'value'
        self.assertEqual(getter(), 'value')

    def test_no_default(self):
        self.assertEqual(os.environ.get('CLASSSETTINGS_ENV'), None)

        @from_env(key='CLASSSETTINGS_ENV')
        def getter(): pass

        self.assertRaises(ImproperlyConfigured, getter)
        os.environ['CLASSSETTINGS_ENV'] = 'value'
        self.assertEqual(getter(), 'value')

    def test_through_with_env(self):
        self.assertEqual(os.environ.get('CLASSSETTINGS_ENV'), None)

        filter_func = lambda val: val.upper()

        @from_env(key='CLASSSETTINGS_ENV', through=filter_func)
        def getter(): pass

        os.environ['CLASSSETTINGS_ENV'] = 'value'
        self.assertEqual(getter(), 'VALUE')

    def test_through_with_default(self):
        self.assertEqual(os.environ.get('CLASSSETTINGS_ENV'), None)

        filter_func = lambda val: val.upper()

        @from_env(key='CLASSSETTINGS_ENV', through=filter_func)
        def getter(): return 'default'

        self.assertEqual(getter(), 'DEFAULT')


class UtilsTestCase(unittest.TestCase):

    def test_defaultargs(self):
        @utils.defaultargs
        def configurable_decorator(*decor_args, **decor_kwargs):
            def decorator(func):
                def decorated(*func_args, **func_kwargs): pass

            return decorator

        def test_func(*func_args, **func_kwargs): pass
        
        funcs = set([configurable_decorator(test_func),
                     configurable_decorator(1)(test_func),
                     configurable_decorator(kwarg=2)(test_func),
                     configurable_decorator(1, kwarg=2)(test_func)])
        self.assertEqual(len(funcs), 1)


class UrlsTestCase(unittest.TestCase):

    def test_url_resolution(self):
        view = lambda request: 'response'

        with Scope(regex='r/') as prefixed_root:
            with Scope(regex='{0}child1/') as child1:
                url('{0}url1/', view)

            with Scope() as child2:
                url('{0}url2/', view)

            url('absolute', view)

        self.assertEqual(len(prefixed_root.urls), 3)
        expected_urls = ('r/child1/url1/', 'r/url2/', 'absolute')
        for url_obj, exp_url in zip(prefixed_root.urls, expected_urls):
            self.assertEqual(url_obj.regex.pattern, exp_url)

        with Scope() as nonprefixed_root:
            self.assertRaises(ImproperlyConfigured, url, '{0}', view)
            url('absolute', view)

        self.assertEqual(nonprefixed_root.urls[0].regex.pattern, 'absolute')

    def test_view_resolution(self):
        
        def modules_view(request):
            return 'modules view'

        def view_callable(request):
            return 'callable view'

        class CBV(object):
            @staticmethod
            def as_view():
                def actual_view(request):
                    return 'cbv view'

                return actual_view

        views_module = type('module', (), {})()
        setattr(views_module, 'view_name', modules_view)
        setattr(views_module, 'view_callable', view_callable)
        setattr(views_module, 'CBV', CBV)

        with Scope() as root:
            with mock.patch('classsettings.urls.inspect.ismodule') as mock_is_module:
                mock_is_module.return_value = True

                with Scope(view=views_module):
                    url('test-url', 'view_name')

            with mock.patch('django.core.urlresolvers.import_module') as mock_import:
                mock_import.return_value = views_module

                with Scope(view='project.app.views'):
                    url('test-url', '{0}.view_callable')
                    url('test-url', view_callable)
                    url('test-url', '{0}.CBV')

            url('test-url', CBV)
            url('test-url', CBV.as_view())

        expected_views = ['modules view', 'callable view', 'callable view',
                          'cbv view', 'cbv view', 'cbv view']
        self.assertEqual([u.callback(None) for u in root.urls], expected_views)

    def test_name_resolution(self):
        view = lambda request: 'response'

        with Scope(name='root') as root_named:
            with Scope() as child1:
                url('test-url', view, name='{0}_child1')

            with Scope(name='{0}_child2'):
                url('test-url', view, name='{0}_url')

            url('test-url', view, name='absolute')

        expected_names = ['root_child1', 'root_child2_url', 'absolute']
        self.assertEqual([u.name for u in root_named.urls], expected_names)

        with Scope() as root_unnamed:
            self.assertRaises(ImproperlyConfigured, url, 'test-url', view, name='{0}')

    def test_context_variables(self):
        view = lambda request: 'response'

        with Scope() as root:
            with Scope(vasyan='foo') as child1:
                self.assertEqual(child1['vasyan'], 'foo')

                with Scope(tadasyan='bar') as child2:
                    self.assertEqual(child2['vasyan'], 'foo')
                    self.assertEqual(child2['tadasyan'], 'bar')

                    with Scope(vasyan='baz') as child3:
                        self.assertEqual(child3['tadasyan'], 'bar')
                        self.assertEqual(child3['vasyan'], 'baz')

                        url('{vasyan}{tadasyan}', view)
                        child3['tadasyan'] = 'xxx'
                        url('{vasyan}{tadasyan}', view)

                    url('{vasyan}{tadasyan}', view)

                self.assertRaises(KeyError, child1.__getitem__, 'tadasyan')
                self.assertRaises(ImproperlyConfigured, url, '{tadasyan}', view)

            self.assertRaises(KeyError, root.__getitem__, 'vasyan')
            self.assertRaises(ImproperlyConfigured, url, '{vasyan}', view)

        expected_urls = ['bazbar', 'bazxxx', 'foobar']
        self.assertEqual([u.regex.pattern for u in root.urls], expected_urls)

    def test_full_resolution(self):
        view = lambda request: 'response'

        with Scope(regex='url') as root:
            with Scope(name='name'):
                with Scope(view=view):
                    url('{0}', view, name='{0}')

        self.assertEqual([u.regex.pattern for u in root.urls], ['url'])
        self.assertEqual([u.callback for u in root.urls], [view])
        self.assertEqual([u.name for u in root.urls], ['name'])

    def test_context_passthrough(self):
        with Scope(regex='a', view='b', name='c') as root:
            with Scope():
                with Scope():
                    with Scope():
                        url('{0}', '{0}', name='{0}')

        u = root.urls[0]
        self.assertTrue(u.regex.pattern == 'a' and u.callback == 'b' and u.name == 'c')

    @skipIf(IS_ABOVE_26, '')
    def test_str_format_under_27(self):
        view = lambda request: 'response'

        with Scope(regex='test') as root:
            self.assertRaises(ImproperlyConfigured, url, '{}', view)

    def test_context(self):
        root = Context(one=1, two=2)
        child = Context(root, one='child 1', three=3)
        def parent_setter(this, new_parent): this.parent = new_parent
        self.assertRaises(TypeError, parent_setter, child, dict())

        self.assertTrue('one' in child.__str__())
        self.assertTrue('one' in child.__repr__())
        self.assertEqual(root['one'], 1)
        self.assertEqual(child['one'], 'child 1')
        self.assertEqual(child.dict(), dict(one='child 1', two=2, three=3))
        self.assertEqual(set(child.keys()), set('one two three'.split()))
        self.assertRaises(KeyError, child.__getitem__, 'not exists')

if __name__ == '__main__':
    unittest.main()
