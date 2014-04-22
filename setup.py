from setuptools import setup, find_packages


setup(
    name = 'django-classsettings',
    version = '1.0.2',
    author='Dmitriy Ferens',
    author_email='ferensdima@gmail.com',
    description = 'Adds ability to define Django settings with classes'
                  '/functions and navigate each of them easily',
    long_description = open('README.rst').read(),
    license='MIT',
    platforms=['Any'],
    url='https://github.com/dferens/django-classsettings',
    download_url='https://pypi.python.org/pypi/django-classsettings',
    packages=find_packages(),
    package_data={'': ['LICENSE', 'README.rst']},
    include_package_data=True,
    install_requires=['Django>=1.4,<1.7'],
    zip_safe=True,
    classifiers=(
        'Development Status :: 2 - Pre-Alpha',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ),
)
