====================
django-classsettings
====================

.. image:: https://travis-ci.org/dferens/django-classsettings.png?branch=master
    :target: https://travis-ci.org/dferens/django-classsettings

.. image:: https://coveralls.io/repos/dferens/django-classsettings/badge.png?branch=master
    :target: https://coveralls.io/r/dferens/django-classsettings?branch=master

Adds ability to define Django settings with classes.

As many text editors and IDEs indexes code symbols, with such approach you can
easily navigate to any group and any line of your settings file.

Settings class
--------------

Exports defined variables into module's scope:

.. code-block:: python

    from classsettings import Settings
    
    class Administration(Settings):
        def ADMINS(self): return (
            ('Your Name', 'your_email@example.com'),
        )
        def DEBUG(self): return False
        def TEMPLATE_DEBUG(self): return self.DEBUG()

Will result in

.. code-block:: python

    ADMINS = (
        ('Your Name', 'your_email@example.com'),
    )
    DEBUG = False
    TEMPLATE_DEBUG = False

Config class
------------

Injects dictionary if variables into module's scope:

.. code-block:: python

    from classsettings import Config
    
    class REST_FRAMEWORK(Config):
        def DEFAULT_FILTER_BACKENDS(self): return (
            'rest_framework.filters.DjangoFilterBackend',
        )

Will result in

.. code-block:: python

    REST_FRAMEWORK = {
        'DEFAULT_FILTER_BACKENDS': (
            'rest_framework.filter.DjangoFilterBackend',
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
        def VAR_NAME(self): pass
