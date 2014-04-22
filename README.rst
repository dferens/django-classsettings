====================
django-classsettings
====================

.. image:: https://travis-ci.org/dferens/django-classsettings.png?branch=master
    :target: https://travis-ci.org/dferens/django-classsettings

.. image:: https://coveralls.io/repos/dferens/django-classsettings/badge.png?branch=master
    :target: https://coveralls.io/r/dferens/django-classsettings?branch=master

Just a collection of Django settings helpers.

1. `Requirements`_.
2. `Settings`_.
3. `urlconfs helpers`_.

Requirements
------------

- Python 2.6, 2.7, 3.2, 3.3
- Django 1.4-1.6

Settings
--------

Settings class - adds ability to group Django settings with classes. As many text editors and IDEs indexes code symbols, with such approach you can
easily navigate to any group and any line of your settings file.

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

Config class - injects dictionary of variables into module's scope:

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

And some decorators may be found usefull:

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


urlconfs helpers
----------------

.. _urlconfs:


Sample urlconf:

.. code-block:: python

    from django.conf.urls import patterns, url

    import views

    urlpatterns = patterns('',
        url(r'^$', views.ProjectList.as_view(), name='projects_project_list'),

        url(r'^create/$', views.ProjectCreate.as_view(), name='projects_project_create'),
        url(r'^view/(?P<pk>\w+)/$', views.ProjectDetail.as_view(), name='projects_project_view'),
        url(r'^update/(?P<pk>\w+)/$', views.ProjectUpdate.as_view(), name='projects_project_update'),
        url(r'^delete/(?P<pk>\w+)/$', views.ProjectDelete.as_view(), name='projects_project_delete'),

        url('^accounts/(?P<pk>\d+)/$', 'project.accounts.profile_info', name='users_info')
        url('^accounts/edit/$', 'project.accounts.profile_edit', name='users_edit')
    )

is equivalent to

.. code-block:: python

    from classsettings.urls import Scope, url

    import views

    #
    # Define url pattern, views or view name prefix:
    #
    # Views resolution:
    #
    #   some.module, 'string' => getattr(module, 'string')
    #   'scope_str', 'string' => 'string'.format('scope_str', ...)
    #
    with Scope(regex='^', views=views, name='projects') as root:
        #
        # Strings are formatted with `str.format`:
        #
        #   value.format(value_of_parent_scope, **scope.context)
        #
        # Additional context variables can be defined and used with `{variable}`
        with Scope(name='{}_project', pk=r'(?P<pk>\w+)') as project:
            # Also supported
            project['pk'] = r'(?P<pk>\w+)'

            # For CBV `.as_view()` is called automatically
            url('{}$', 'ProjectList', name='{}_list')  # url => '^$', name => 'projects_project_list' 
            url('{}create/$', 'ProjectCreate', name='{}_create')
            url('{}view/{pk}/$', 'ProjectDetail', name='{}_detail')
            url('{}update/{pk}/$', 'ProjectUpdate', name='{}_update')
            url('{}delete/{pk}/$', 'ProjectDelete', name='{}_delete')

        with Scope(regex='{}accounts/', views='project.accounts', name='users',
                   user_id=r'(?P<pk>\d+)'):
            url('{}{user_id}?/$', '{}.profile_info', name='{}_info')
            url('{}edit/$', '{}.profile_edit', name='{}_edit')

    urlpatterns = root.urls

For urls defined outside *Scope object* native django's url function is used.
