====================
django-classsettings
====================

.. image:: https://travis-ci.org/dferens/django-classsettings.png?branch=master
    :target: https://travis-ci.org/dferens/django-classsettings

.. image:: https://coveralls.io/repos/dferens/django-classsettings/badge.png?branch=master
    :target: https://coveralls.io/r/dferens/django-classsettings?branch=master

Adds ability to group Django settings with classes.

As many text editors and IDEs indexes code symbols, with such approach you can
easily navigate to any group and any line of your settings file.

Settings class
--------------

.. code-block:: python

    class Apps(Settings):
        def DJANGO_APPS(self): return (
            'django.contrib.auth',
             ...
        )
        def THIRD_PARTY_APPS(self): return (
            'rest_framework',
            'south',
        )
        def OWN_APPS(self): return (
            'app1',
            'app2',
        )
        def INSTALLED_APPS(self):
            return self.DJANGO_APPS() + self.THIRD_PARTY_APPS() + self.OWN_APPS()

With **Sublime Text 3** press :code:`Cmd+Shift+R` and type "THIRD".
Same thing could be done with *TEMPLATE_CONTEXT_PROCESSORS*, *MIDDLEWARE_CLASSES* etc.


Config class
------------

Injects dictionary of variables into module's scope:

.. code-block:: python

    from classsettings import Config
    
    class REST_FRAMEWORK(Config):
        def DEFAULT_FILTER_BACKENDS(self): return (
            'rest_framework.filters.DjangoFilterBackend',
        )
        DEFAULT_RENDERER_CLASSES = ('rest_framework.renderers.YAMLRenderer',)

Will result in

.. code-block:: python

    REST_FRAMEWORK = {
        'DEFAULT_FILTER_BACKENDS': (
            'rest_framework.filter.DjangoFilterBackend',
        ),
        'DEFAULT_RENDERER_CLASSES': (
            'rest_framework.renderers.YAMLRenderer',
        )
    }

Decorators
----------

Some decorators may be found usefull:

.. code-block:: python

    from classsettings import Settings, from_env
    
    class MySettingsGroup(Settings):
        # Will look for `EMAIL_HOST` key in `os.environ`
        # and use `smtp.gmail.com` if such key was not found
        @from_env
        def EMAIL_HOST(self): return 'smtp.gmail.com'
        
        # Will raise Django's `ImproperlyConfigured` exception
        # if such key was not found
        @from_env
        def SECRET_KEY(self): pass

        # Will look for specified key
        @from_env(key='CUSTOM_ENV_VAR_NAME')
        def variable(self): pass

        # Will apply `through` callable to result
        @from_env(through=dj_database_url.parse)
        def DATABASE_URL(self): return 'sqlite://'
