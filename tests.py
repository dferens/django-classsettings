import os
import unittest

from django.core.exceptions import ImproperlyConfigured

# from classsettings import settings, from_env, utils
from classsettings import Settings, Config, from_env, utils


class InjectorTestCase(unittest.TestCase):

    def setUp(self):
        self._old_globals = dict(globals())

    def tearDown(self):
        to_delete = [k for k in globals() if k not in self._old_globals]
        map(lambda k: globals().pop(k), to_delete)


class SettingsTestCase(InjectorTestCase):

    def test_fields(self):
        old_module_vars = set(globals())

        class MySettings(Settings):
            def public_method(self): return 1
            def _private_method(self): return 2
            some_field = 2
            class some_class(object): pass

        new_module_vars = set(globals())
        self.assertEqual(new_module_vars - old_module_vars,
                         set(('public_method',)))

    def test_related(self):
        class MySettings(Settings):
          def _private_setting(self): return 1
          def public_setting(self): return self._private_setting() * 2

        self.assertEqual(globals()['public_setting'], 2)


class ConfigTestCase(InjectorTestCase):

    def test_injects(self):
        old_module_vars = set(globals())
        self.assertNotIn('MyConfig', old_module_vars)

        class MyConfig(Config): pass

        new_module_vars = set(globals())
        self.assertEqual(new_module_vars - old_module_vars,
                         set(('MyConfig',)))
        self.assertEqual(globals()['MyConfig'], dict())

    def test_fields(self):
        class MyConfig(Config):
           def public_method(self): return 1
           def _private_method(self): return 2
           some_field = 2
           class some_class(object): pass

        result_dict = globals()['MyConfig']
        self.assertEqual(result_dict, {'public_method': 1})

    def test_related(self):
        class MyConfig(Config):
           def public_setting(self): return self._private_setting() * 2
           def _private_setting(self): return 1

        self.assertEqual(globals()['MyConfig'], {'public_setting': 2})


class FromEnvTestCase(unittest.TestCase):

    def setUp(self):
        self._old_environ = dict(os.environ)

    def tearDown(self):
        to_delete = [k for k in os.environ if k not in self._old_environ]
        map(os.environ.pop, to_delete)

    def test_has_default(self):
        @from_env(key='CLASSSETTINGS_ENV')
        def getter(): return 'default'

        self.assertEqual(getter(), 'default')
        os.environ['CLASSSETTINGS_ENV'] = 'value'
        self.assertEqual(getter(), 'value')

    def test_no_default(self):
        @from_env(key='CLASSSETTINGS_ENV')
        def getter(): pass

        self.assertRaises(ImproperlyConfigured, getter)
        os.environ['CLASSSETTINGS_ENV'] = 'value'
        self.assertEqual(getter(), 'value')


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


if __name__ == '__main__':
    unittest.main()
