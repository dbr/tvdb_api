import sys
from setuptools import setup
from setuptools.command.test import test as TestCommand


class PyTest(TestCommand):
    user_options = [('pytest-args=', 'a', "Arguments to pass to py.test")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = []

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        #import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.pytest_args)
        sys.exit(errno)


_requirements = ['requests_cache', 'requests']
_modules = ['tvdb_api', 'tvdb_ui', 'tvdb_exceptions']


setup(
name = 'tvdb_api',
version='2.0-dev',

author='dbr/Ben',
description='Interface to thetvdb.com',
url='http://github.com/dbr/tvdb_api/tree/master',
license='unlicense',

long_description="""\
An easy to use API interface to TheTVDB.com
Basic usage is:

>>> import tvdb_api
>>> t = tvdb_api.Tvdb()
>>> ep = t['My Name Is Earl'][1][22]
>>> ep
<Episode 01x22 - Stole a Badge>
>>> ep['episodeName']
u'Stole a Badge'
""",

py_modules = _modules,
install_requires = _requirements,

tests_require=['pytest'],
cmdclass = {'test': PyTest},

classifiers=[
    "Intended Audience :: Developers",
    "Natural Language :: English",
    "Operating System :: OS Independent",
    "Programming Language :: Python",
    "Programming Language :: Python :: 2",
    "Programming Language :: Python :: 2.6",
    "Programming Language :: Python :: 2.7",
    "Programming Language :: Python :: 3.3",
    "Programming Language :: Python :: 3.4",
    "Programming Language :: Python :: 3.5",
    "Programming Language :: Python :: 3.6",
    "Topic :: Multimedia",
    "Topic :: Utilities",
    "Topic :: Software Development :: Libraries :: Python Modules",
]
)
