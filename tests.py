import os
import unittest

from django.core.exceptions import ImproperlyConfigured

from classsettings import settings, from_env, utils


class SettingsTestCase(unittest.TestCase):

    def setUp(self):
        self._old_globals = globals()

    def tearDown(self):
        new_globals = globals()
        for key in new_globals:
            if key not in self._old_globals:
                del new_globals[key]

    def test_public(self):
        old_module_vars = set(globals())
        self.assertNotIn('setting_name', old_module_vars)

        @settings()
        class MySettings(object):
          def setting_name(self): return 1

        new_module_vars = set(globals())
        self.assertEqual(new_module_vars - old_module_vars,
                         set(('setting_name',)))

    def test_not_importable(self):
        old_module_vars = set(globals())
        self.assertNotIn('_private_method', old_module_vars)

        @settings()
        class MySettings(object):
          def _private_method(self): return 1
          some_field = 2
          class some_class(object): pass

        new_module_vars = set(globals())
        self.assertEqual(new_module_vars, old_module_vars)

    def test_related(self):
        old_module_vars = set(globals())
        self.assertNotIn('_private_setting', old_module_vars)

        @settings()
        class MySettings(object):
          def _private_setting(self): return 1
          def public_setting(self): return self._private_setting() * 2

        new_module_globals = globals()
        self.assertEqual(new_module_globals['public_setting'], 2)

    def test_dict_mode(self):
        old_module_vars = set(globals())
        self.assertNotIn('setting_name', old_module_vars)

        @settings(to_dict=True)
        class MySettings(object):
          def setting_name(self): return 1

        new_module_globals = globals()
        self.assertEqual(set(new_module_globals) - old_module_vars,
                         set(('MySettings',)))
        self.assertEqual(new_module_globals['MySettings'], {'setting_name': 1})


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
