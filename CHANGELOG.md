# Changelog

## `3.0` - unreleased

- Important: Your own API key is now required to use this module. The default shared API key has been removed.
  Keys are easy to register via https://thetvdb.com/api-information
- Include cache location info in debug logging
- Drop support for Python 2.6 (EOL 2016), 3.3 (EOL 2013), 3.4 (EOL 2019)

## `2.1` - 2018-03-10

- Began keeping change log
- Correctly errors when failing to find show by ID -
  [issue #54](https://github.com/dbr/tvdb_api/issues/54)
- Web cache filename contains major version of Python to support
  side-by-side usage of `tvdb_api` in Python 2 and 3

## `2.0` - 2017-09-16

- Switch to TheTVDB new JSON based API -
  [issue #57](https://github.com/dbr/tvdb_api/issues/57)
