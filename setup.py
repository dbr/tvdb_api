import sys
from setuptools import setup

# Load README
from os import path
this_directory = path.abspath(path.dirname(__file__))
if sys.version_info[0] == 2:
    with open(path.join(this_directory, 'README.md')) as f:
        long_description = f.read().decode("utf-8")
else:
    with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
        long_description = f.read()

setup(
    name='tvdb_api',
    version='3.1.0',

    author='dbr/Ben',
    description='Interface to thetvdb.com',
    url='http://github.com/dbr/tvdb_api',

    long_description=long_description,
    long_description_content_type='text/markdown',

    py_modules=['tvdb_api'],
    install_requires=['requests_cache~=0.9.6', 'requests~=2.28.1'],

    classifiers=[
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Multimedia",
        "Topic :: Utilities",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: Public Domain",
    ]
)
