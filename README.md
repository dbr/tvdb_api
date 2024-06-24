# `tvdb_api`
[![PyPI][pypi-img]][pypi-link] [![Build Status][travis-img]][travis-link] [![codecov][coverage-img]][coverage-link]

`tvdb_api` is an easy to use interface to [thetvdb.com][tvdb]

It supports Python 3.9 onwards

`tvnamer` has moved to a separate repository: [github.com/dbr/tvnamer][tvnamer] - it is a utility which uses `tvdb_api` to rename files from `some.show.s01e03.blah.abc.avi` to `Some Show - [01x03] - The Episode Name.avi` (which works by getting the episode name from `tvdb_api`)


[tvdb]: http://thetvdb.com
[tvnamer]: http://github.com/dbr/tvnamer
[travis-link]: https://travis-ci.com/dbr/tvdb_api
[travis-img]: https://travis-ci.com/dbr/tvdb_api.svg?branch=master
[pypi-link]: https://pypi.org/project/tvdb-api/
[pypi-img]: https://img.shields.io/pypi/v/tvdb_api
[coverage-link]: https://codecov.io/gh/dbr/tvdb_api
[coverage-img]: https://codecov.io/gh/dbr/tvdb_api/branch/master/graph/badge.svg


## To install

You can easily install `tvdb_api` via `pip`

    pip install --upgrade tvdb_api

You may need to use sudo, depending on your setup:

    sudo pip install --upgrade tvdb_api

On Debian distro pip have been desactivated outside virtual environement.

    python -m venv /path/to/new/virtual/environment
     then proceed with the packe installation via pip

## Basic usage

First initialise an instance of the `Tvdb` class with your API key:

    import tvdb_api
    t = tvdb_api.Tvdb() 

Note you must specify the apikey argument here, for example:

    t = Tvdb(apikey="ENTER YOUR API KEY HERE") # doctest:+SKIP

See https://thetvdb.com/api-information to register a key.

Then to use the API:

    episode = t['My Name Is Earl'][1][3] # get season 1, episode 3 of show
    print episode['episodename'] # Print episode name

## Registering an API key

You must have an API key from <http://thetvdb.com> in order to use this module.

Registering for a key is easy to do and can be done within a few minutes - see the following page for details:

<https://thetvdb.com/api-information>

Note: In `tvdb_api` v2 a default key was included for convenience. However over time this key became very heavily used and this causes problems for TheTVDB.com admins. This old shared key will be deprecated and removed at some point soon.

## Advanced usage

Most of the documentation is in docstrings. The examples are tested (using doctest) so will always be up to date and working.

The docstring for `Tvdb.__init__` lists all initialisation arguments, including support for non-English searches, custom "Select Series" interfaces and enabling the retrieval of banners and extended actor information. You can also override the default API key using `apikey`, recommended if you're using `tvdb_api` in a larger script or application

### Exceptions

There are several exceptions you may catch, these can be imported from `tvdb_api`:

- `tvdb_error` - this is raised when there is an error communicating with [thetvdb.com][tvdb] (a network error most commonly)
- `tvdb_userabort` - raised when a user aborts the Select Series dialog (by `ctrl+c`, or entering `q`)
- `tvdb_shownotfound` - raised when `t['show name']` cannot find anything
- `tvdb_seasonnotfound` - raised when the requested series (`t['show name][99]`) does not exist
- `tvdb_episodenotfound` - raised when the requested episode (`t['show name][1][99]`) does not exist.
- `tvdb_attributenotfound` - raised when the requested attribute is not found (`t['show name']['an attribute']`, `t['show name'][1]['an attribute']`, or ``t['show name'][1][1]['an attribute']``)

### Series data

All data exposed by [thetvdb.com][tvdb] is accessible via the `Show` class. A Show is retrieved by doing..

    >>> import tvdb_api
    >>> t = tvdb_api.Tvdb()
    >>> show = t['scrubs']
    >>> type(show)
    <class 'tvdb_api.Show'>

For example, to find out what network Scrubs is aired:

    >>> t['scrubs']['network']
    'ABC'

The data is stored in an attribute named `data`, within the Show instance:

    >>> t['scrubs'].data.keys()
    ['networkid', 'rating', 'airs_dayofweek', 'contentrating', 'seriesname', 'id', 'airs_time', 'network', 'fanart', 'lastupdated', 'actors', 'ratingcount', 'status', 'added', 'poster', 'tms_wanted_old', 'imdb_id', 'genre', 'banner', 'seriesid', 'language', 'zap2it_id', 'addedby', 'firstaired', 'runtime', 'overview']

Although each element is also accessible via `t['scrubs']` for ease-of-use:

    >>> t['scrubs']['rating']
    '9.0'

This is the recommended way of retrieving "one-off" data (for example, if you are only interested in "seriesname"). If you wish to iterate over all data, or check if a particular show has a specific piece of data, use the `data` attribute,

    >>> 'rating' in t['scrubs'].data
    True

### Banners and actors

Since banners and actors are separate XML files, retrieving them by default is undesirable. If you wish to retrieve banners (and other fanart), use the `banners` Tvdb initialisation argument:

    >>> from tvdb_api import Tvdb
    >>> t = Tvdb(banners = True)

Then access the data using a `Show`'s `_banner` key:

    >>> t['scrubs']['_banners'].keys()
    ['fanart', 'poster', 'series', 'season']

The banner data structure will be improved in future versions.

Extended actor data is accessible similarly:

    >>> t = Tvdb(actors = True)
    >>> actors = t['scrubs']['_actors']
    >>> actors[0]
    <Actor "Zach Braff">
    >>> actors[0].keys()
    ['sortorder', 'image', 'role', 'id', 'name']
    >>> actors[0]['role']
    'Dr. John Michael "J.D." Dorian'

Remember a simple list of actors is accessible via the default Show data:

    >>> t['scrubs']['actors']
    '|Zach Braff|Donald Faison|Sarah Chalke|Judy Reyes|John C. McGinley|Neil Flynn|Ken Jenkins|Christa Miller|Aloma Wright|Robert Maschio|Sam Lloyd|Travis Schuldt|Johnny Kastl|Heather Graham|Michael Mosley|Kerry Bish\xe9|Dave Franco|Eliza Coupe|'
