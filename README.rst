django-classsettings
====================

Adds ability to define Django settings with classes like this::

  from classsettings import Settings
  
  class Static(Settings):
      def STATIC_URL(self): return '/static/'

  # Transforms into
  STATIC_URL = '/static/'

As many text editors and IDEs indexes code symbols, with such approach you can
easily navigate to any group and any line of your settings file.
