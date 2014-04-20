import os
import unittest

from django.core.exceptions import ImproperlyConfigured

from classsettings import Settings, Config, from_env, utils


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


if __name__ == '__main__':
    unittest.main()
