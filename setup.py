import sys
from setuptools import setup

IS_PY2 = sys.version_info[0] == 2

_requirements = []
if not IS_PY2:
    _requirements.append('requests_cache')

    # 'requests' is installed as requirement by requests-cache,
    # commented out because it triggers a bug in setuptool:
    # https://bitbucket.org/pypa/setuptools/issue/196/tests_require-pytest-pytest-cov-breaks


_modules = ['tvdb_api', 'tvdb_ui', 'tvdb_exceptions']
if IS_PY2:
    _modules.append('tvdb_cache')


setup(
name = 'tvdb_api',
version='1.10',

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
>>> ep['episodename']
u'Stole a Badge'
""",

py_modules = _modules,
install_requires = _requirements,

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
    "Topic :: Multimedia",
    "Topic :: Utilities",
    "Topic :: Software Development :: Libraries :: Python Modules",
]
)
