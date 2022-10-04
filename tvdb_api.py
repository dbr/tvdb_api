#!/usr/bin/env python
# encoding:utf-8
# author:dbr/Ben
# project:tvdb_api
# repository:http://github.com/dbr/tvdb_api
# license:unlicense (http://unlicense.org/)

"""Simple-to-use Python interface to The TVDB's API (thetvdb.com)

Example usage:

>>> from tvdb_api import Tvdb
>>> t = Tvdb()
>>> t['Scrubs'][1][4]['episodeName']
'The Hotel Inspectors'
"""

__author__ = "dbr/Ben"
__version__ = "3.1.0"


import sys
import os
import time
import getpass
import tempfile
import logging
from urllib.parse import quote as url_quote

import requests
import requests_cache


LOG = logging.getLogger("tvdb_api")


# Exceptions


class TvdbBaseException(Exception):
    """Base exception for all tvdb_api errors
    """

    pass


class TvdbError(TvdbBaseException):
    """An error with thetvdb.com (Cannot connect, for example)
    """

    pass


class TvdbUserAbort(TvdbBaseException):
    """User aborted the interactive selection (via
    the q command, ^c etc)
    """

    pass


class TvdbNotAuthorized(TvdbBaseException):
    """An authorization error with thetvdb.com
    """

    pass


class TvdbDataNotFound(TvdbBaseException):
    """Base for all attribute-not-found errors (e.gg missing show/season/episode/data)
    """

    pass


class TvdbShowNotFound(TvdbDataNotFound):
    """Show cannot be found on thetvdb.com (non-existent show)
    """

    pass


class TvdbSeasonNotFound(TvdbDataNotFound):
    """Season cannot be found on thetvdb.com
    """

    pass


class TvdbEpisodeNotFound(TvdbDataNotFound):
    """Episode cannot be found on thetvdb.com
    """

    pass


class TvdbResourceNotFound(TvdbDataNotFound):
    """Resource cannot be found on thetvdb.com
    """

    pass


class TvdbAttributeNotFound(TvdbDataNotFound):
    """Raised if an episode does not have the requested
    attribute (such as a episode name)
    """

    pass

# UI


class BaseUI(object):
    """Base user interface for Tvdb show selection.

    Selects first show.

    A UI is a callback. A class, it's __init__ function takes two arguments:

    - config, which is the Tvdb config dict, setup in tvdb_api.py
    - log, which is Tvdb's logger instance (which uses the logging module). You can
    call log.info() log.warning() etc

    It must have a method "selectSeries", this is passed a list of dicts, each dict
    contains the the keys "name" (human readable show name), and "sid" (the shows
    ID as on thetvdb.com). For example:

    [{'name': 'Lost', 'sid': '73739'},
     {'name': 'Lost Universe', 'sid': '73181'}]

    The "selectSeries" method must return the appropriate dict, or it can raise
    TvdbUserAbort (if the selection is aborted), TvdbShowNotFound (if the show
    cannot be found).

    A simple example callback, which returns a random series:

    >>> import random
    >>> from tvdb_ui import BaseUI
    >>> class RandomUI(BaseUI):
    ...    def selectSeries(self, allSeries):
    ...            import random
    ...            return random.choice(allSeries)

    Then to use it..

    >>> from tvdb_api import Tvdb
    >>> t = Tvdb(custom_ui = RandomUI)
    >>> random_matching_series = t['Scrubs']
    >>> type(random_matching_series)
    <class 'tvdb_api.Show'>
    """

    def __init__(self, config):
        self.config = config

    def selectSeries(self, allSeries):  # noqa: N802 # Deprecated
        """Deprecated: use `select_series` method instead
        """
        return self.select_series(all_series=allSeries)

    def select_series(self, all_series):
        return all_series[0]


class ConsoleUI(BaseUI):
    """Interactively allows the user to select a show from a console based UI
    """

    def _display_series(self, allSeries, limit=6):
        """Helper function, lists series with corresponding ID
        """
        if limit is not None:
            toshow = allSeries[:limit]
        else:
            toshow = allSeries

        print("TVDB Search Results:")
        for i, cshow in enumerate(toshow):
            i_show = i + 1  # Start at more human readable number 1 (not 0)
            LOG.debug('Showing allSeries[%s], series %s)' % (i_show, allSeries[i]['seriesName']))
            if i == 0:
                extra = " (default)"
            else:
                extra = ""

            output = "%s -> %s [%s] # http://thetvdb.com/?tab=series&id=%s%s" % (
                i_show,
                cshow['seriesName'],
                cshow['language'],
                str(cshow['id']),
                extra,
            )
            print(output)

    def selectSeries(self, allSeries):  # noqa: N802 # Deprecated
        """Deprecated: use `select_series` method instead
        """

        return self.select_series(all_series=allSeries)

    def select_series(self, all_series):  # noqa: N802 # Deprecated
        self._display_series(all_series)

        if len(all_series) == 1:
            # Single result, return it!
            print("Automatically selecting only result")
            return all_series[0]

        if self.config['select_first'] is True:
            print("Automatically returning first search result")
            return all_series[0]

        while True:  # return breaks this loop
            try:
                print("Enter choice (first number, return for default, 'all', ? for help):")
                ans = input()
            except KeyboardInterrupt:
                raise TvdbUserAbort("User aborted (^c keyboard interupt)")
            except EOFError:
                raise TvdbUserAbort("User aborted (EOF received)")

            LOG.debug('Got choice of: %s' % (ans))
            try:
                selected_id = int(ans) - 1  # The human entered 1 as first result, not zero
            except ValueError:  # Input was not number
                if len(ans.strip()) == 0:
                    # Default option
                    LOG.debug('Default option, returning first series')
                    return all_series[0]
                if ans == "q":
                    LOG.debug('Got quit command (q)')
                    raise TvdbUserAbort("User aborted ('q' quit command)")
                elif ans == "?":
                    print("## Help")
                    print("# Enter the number that corresponds to the correct show.")
                    print("# a - display all results")
                    print("# all - display all results")
                    print("# ? - this help")
                    print("# q - abort tvnamer")
                    print("# Press return with no input to select first result")
                elif ans.lower() in ["a", "all"]:
                    self._display_series(all_series, limit=None)
                else:
                    LOG.debug('Unknown keypress %s' % (ans))
            else:
                LOG.debug('Trying to return ID: %d' % (selected_id))
                try:
                    return all_series[selected_id]
                except IndexError:
                    LOG.debug('Invalid show number entered!')
                    print("Invalid number (%s) selected!")
                    self._display_series(all_series)


# Main API


class ShowContainer(dict):
    """Simple dict that holds a series of Show instances
    """

    def __init__(self):
        self._stack = []
        self._lastgc = time.time()

    def __setitem__(self, key, value):
        self._stack.append(key)

        # keep only the 100th latest results
        if time.time() - self._lastgc > 20:
            for o in self._stack[:-100]:
                del self[o]
            self._stack = self._stack[-100:]

            self._lastgc = time.time()

        super(ShowContainer, self).__setitem__(key, value)


class Show(dict):
    """Holds a dict of seasons, and show data.
    """

    def __init__(self):
        dict.__init__(self)
        self.data = {}

    def __repr__(self):
        return "<Show %r (containing %s seasons)>" % (
            self.data.get('seriesName', 'instance'),
            len(self),
        )

    def __getitem__(self, key):
        if key in self:
            # Key is an episode, return it
            return dict.__getitem__(self, key)

        if key in self.data:
            # Non-numeric request is for show-data
            return dict.__getitem__(self.data, key)

        # Data wasn't found, raise appropriate error
        if isinstance(key, int) or key.isdigit():
            # Episode number x was not found
            raise TvdbSeasonNotFound("Could not find season %s" % (repr(key)))
        else:
            # If it's not numeric, it must be an attribute name, which
            # doesn't exist, so attribute error.
            raise TvdbAttributeNotFound("Cannot find attribute %s" % (repr(key)))

    def aired_on(self, date):
        ret = self.search(str(date), 'firstAired')
        if len(ret) == 0:
            raise TvdbEpisodeNotFound("Could not find any episodes that aired on %s" % date)
        return ret

    def search(self, term=None, key=None):
        """
        Search all episodes in show. Can search all data, or a specific key
        (for example, episodename)

        Always returns an array (can be empty). First index contains the first
        match, and so on.

        Each array index is an Episode() instance, so doing
        search_results[0]['episodename'] will retrieve the episode name of the
        first match.

        Search terms are converted to lower case (unicode) strings.

        # Examples

        These examples assume t is an instance of Tvdb():

        >>> t = Tvdb()
        >>>

        To search for all episodes of Scrubs with a bit of data
        containing "my first day":

        >>> t['Scrubs'].search("my first day")
        [<Episode 01x01 - 'My First Day'>]
        >>>

        Search for "My Name Is Earl" episode named "Faked His Own Death":

        >>> t['My Name Is Earl'].search('Faked My Own Death', key='episodeName')
        [<Episode 01x04 - 'Faked My Own Death'>]
        >>>

        To search Scrubs for all episodes with "mentor" in the episode name:

        >>> t['scrubs'].search('mentor', key='episodeName')
        [<Episode 01x02 - 'My Mentor'>, <Episode 03x15 - 'My Tormented Mentor'>]
        >>>

        # Using search results

        >>> results = t['Scrubs'].search("my first")
        >>> print results[0]['episodeName']
        My First Day
        >>> for x in results: print x['episodeName']
        My First Day
        My First Step
        My First Kill
        >>>
        """
        results = []
        for cur_season in self.values():
            searchresult = cur_season.search(term=term, key=key)
            if len(searchresult) != 0:
                results.extend(searchresult)

        return results


class Season(dict):
    def __init__(self, show=None):
        """The show attribute points to the parent show
        """
        self.show = show

    def __repr__(self):
        return "<Season instance (containing %s episodes)>" % (len(self.keys()))

    def __getitem__(self, episode_number):
        if episode_number not in self:
            raise TvdbEpisodeNotFound("Could not find episode %s" % (repr(episode_number)))
        else:
            return dict.__getitem__(self, episode_number)

    def search(self, term=None, key=None):
        """Search all episodes in season, returns a list of matching Episode
        instances.

        >>> t = Tvdb()
        >>> t['scrubs'][1].search('first day')
        [<Episode 01x01 - 'My First Day'>]
        >>>

        See Show.search documentation for further information on search
        """
        results = []
        for ep in self.values():
            searchresult = ep.search(term=term, key=key)
            if searchresult is not None:
                results.append(searchresult)
        return results


class Episode(dict):
    def __init__(self, season=None):
        """The season attribute points to the parent season
        """
        self.season = season

    def __repr__(self):
        seasno = self.get('airedSeason', 0)
        epno = self.get('airedEpisodeNumber', 0)
        epname = self.get('episodeName')
        if epname is not None:
            return "<Episode %02dx%02d - %r>" % (seasno, epno, epname)
        else:
            return "<Episode %02dx%02d>" % (seasno, epno)

    def __getitem__(self, key):
        try:
            return dict.__getitem__(self, key)
        except KeyError:
            raise TvdbAttributeNotFound("Cannot find attribute %s" % (repr(key)))

    def search(self, term=None, key=None):
        """Search episode data for term, if it matches, return the Episode (self).
        The key parameter can be used to limit the search to a specific element,
        for example, episodename.

        This primarily for use use by Show.search and Season.search. See
        Show.search for further information on search

        Simple example:

        >>> e = Episode()
        >>> e['episodeName'] = "An Example"
        >>> e.search("examp")
        <Episode 00x00 - 'An Example'>
        >>>

        Limiting by key:

        >>> e.search("examp", key = "episodeName")
        <Episode 00x00 - 'An Example'>
        >>>
        """
        if term is None:
            raise TypeError("must supply string to search for (contents)")

        term = str(term).lower()
        for cur_key, cur_value in self.items():
            cur_key = str(cur_key)
            cur_value = str(cur_value).lower()
            if key is not None and cur_key != key:
                # Do not search this key
                continue
            if cur_value.find(str(term)) > -1:
                return self


class Actors(list):
    """Holds all Actor instances for a show
    """

    pass


class Actor(dict):
    """Represents a single actor. Should contain..

    id,
    image,
    name,
    role,
    sortorder
    """

    def __repr__(self):
        return "<Actor %r>" % self.get("name")


class Tvdb:
    """Create easy-to-use interface to name of season/episode name
    >>> t = Tvdb()
    >>> t['Scrubs'][1][24]['episodeName']
    'My Last Day'
    """

    def __init__(
        self,
        interactive=False,
        select_first=False,
        cache=True,
        banners=False,
        actors=False,
        custom_ui=None,
        language=None,
        apikey=None,
        username=None,
        userkey=None,
        dvdorder=False,
    ):

        """interactive (True/False):
            When True, uses built-in console UI is used to select the correct show.
            When False, the first search result is used.

        select_first (True/False):
            Automatically selects the first series search result (rather
            than showing the user a list of more than one series).
            Is overridden by interactive = False, or specifying a custom_ui

        cache (True/False/str/requests_cache.CachedSession):

            Retrieved URLs can be persisted to to disc.

            True/False enable or disable default caching. Passing
            string specifies the directory where to store the
            "tvdb.sqlite3" cache file. Alternatively a custom
            requests.Session instance can be passed (e.g maybe a
            customised instance of `requests_cache.CachedSession`)

        banners (True/False):
            Retrieves the banners for a show. These are accessed
            via the _banners key of a Show(), for example:

            >>> Tvdb(banners=True)['scrubs']['_banners'].keys()
            ['fanart', 'poster', 'seasonwide', 'season', 'series']

        actors (True/False):
            Retrieves a list of the actors for a show. These are accessed
            via the _actors key of a Show(), for example:

            >>> t = Tvdb(actors=True)
            >>> t['scrubs']['_actors'][0]['name']
            'John C. McGinley'

        custom_ui (tvdb_ui.BaseUI subclass):
            A callable subclass of tvdb_ui.BaseUI (overrides interactive option)

        language (2 character language abbreviation):
            The 2 digit language abbreviation used for the returned data,
            and is also used when searching. For a complete list, call
            the `Tvdb.available_languages` method.
            Default is "en" (English).

        apikey (str/unicode):
            Your API key for TheTVDB. You can easily register a key with in
            a few minutes:
            https://thetvdb.com/api-information

        username (str/unicode or None):
            Specify a user account to use for actions which require
            authentication (e.g marking a series as favourite, submitting ratings)

        userkey (str/unicode, or None):
            User authentication key relating to "username".
        """

        self.shows = ShowContainer()  # Holds all Show classes
        self.corrections = {}  # Holds show-name to show_id mapping

        self.config = {}

        # Ability to pull key from env-var mostly for unit-tests
        _test_key = os.getenv('TVDB_API_KEY')
        if apikey is None and _test_key is not None:
            apikey = _test_key

        if apikey is None:
            raise ValueError(
                (
                    "apikey argument is now required - an API key can be easily registered "
                    "at https://thetvdb.com/api-information"
                )
            )
        self.config['auth_payload'] = {
            "apikey": apikey,
            "username": username or "",
            "userkey": userkey or "",
        }

        self.config['custom_ui'] = custom_ui

        self.config['interactive'] = interactive  # prompt for correct series?

        self.config['select_first'] = select_first

        self.config['dvdorder'] = dvdorder

        if cache is True:
            cache_dir = self._get_temp_dir()
            LOG.debug("Caching using requests_cache to %s" % cache_dir)
            self.session = requests_cache.CachedSession(
                expire_after=21600,  # 6 hours
                backend='sqlite',
                cache_name=cache_dir,
                include_get_headers=True,
            )
            self.session.remove_expired_responses()
            self.config['cache_enabled'] = True
        elif cache is False:
            LOG.debug("Caching disabled")
            self.session = requests.Session()
            self.config['cache_enabled'] = False
        elif isinstance(cache, str):
            LOG.debug("Caching using requests_cache to specified directory %s" % cache)
            # Specified cache path
            self.session = requests_cache.CachedSession(
                expire_after=21600,  # 6 hours
                backend='sqlite',
                cache_name=os.path.join(cache, "tvdb_api"),
                include_get_headers=True,
            )
            self.session.remove_expired_responses()
        else:
            LOG.debug("Using specified requests.Session")
            self.session = cache
            try:
                self.session.get
            except AttributeError:
                raise ValueError(
                    (
                        "cache argument must be True/False, string as cache path "
                        "or requests.Session-type object (e.g from requests_cache.CachedSession)"
                    )
                )

        self.config['banners_enabled'] = banners
        self.config['actors_enabled'] = actors

        if language is None:
            self.config['language'] = 'en'
        else:
            self.config['language'] = language

        # The following url_ configs are based of the
        # https://api.thetvdb.com/swagger
        self.config['base_url'] = "http://thetvdb.com"
        self.config['api_url'] = "https://api.thetvdb.com"

        self.config['url_getSeries'] = u"%(api_url)s/search/series?name=%%s" % self.config

        self.config['url_epInfo'] = u"%(api_url)s/series/%%s/episodes" % self.config

        self.config['url_seriesInfo'] = u"%(api_url)s/series/%%s" % self.config
        self.config['url_actorsInfo'] = u"%(api_url)s/series/%%s/actors" % self.config

        self.config['url_seriesBanner'] = u"%(api_url)s/series/%%s/images" % self.config
        self.config['url_seriesBannerInfo'] = (
            u"%(api_url)s/series/%%s/images/query?keyType=%%s" % self.config
        )
        self.config['url_artworkPrefix'] = u"%(base_url)s/banners/%%s" % self.config

        self.__authorized = False
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Accept-Language': self.config['language'],
        }

    def _get_temp_dir(self):
        """Returns the [system temp dir]/tvdb_api-u501 (or
        tvdb_api-myuser)
        """
        py_major = sys.version_info[
            0
        ]  # Prefix with major version as 2 and 3 write incompatible caches
        if hasattr(os, 'getuid'):
            uid = "-u%d" % (os.getuid())
        else:
            # For Windows
            uid = getpass.getuser()

        return os.path.join(tempfile.gettempdir(), "tvdb_api-%s-py%s" % (uid, py_major))

    def _load_url(self, url, data=None, language=None):
        """Return response from The TVDB API"""

        if not language:
            language = self.config['language']
        self.headers['Accept-Language'] = language

        # TODO: Handle Exceptions
        # TODO: Update Token

        # encoded url is used for hashing in the cache so
        # python 2 and 3 generate the same hash
        if not self.__authorized:
            # only authorize if we haven't before and we
            # don't have the url in the cache
            fake_session_for_key = requests.Session()
            fake_session_for_key.headers['Accept-Language'] = language
            cache_key = None
            try:
                # in case the session class has no cache object, fail gracefully
                cache_key = self.session.cache.create_key(
                    fake_session_for_key.prepare_request(requests.Request('GET', url))
                )
            except Exception:
                # FIXME: Can this just check for hasattr(self.session, "cache") instead?
                pass

            # fmt: off
            # No fmt because mangles noqa comment - https://github.com/psf/black/issues/195
            if not cache_key or not self.session.cache.has_key(cache_key): # noqa: not a dict, has_key is part of requests-cache API
                self.authorize()
            # fmt: on

        response = self.session.get(url, headers=self.headers)
        r = response.json()
        LOG.debug("loadurl: %s language=%s" % (url, language))
        LOG.debug("response:")
        LOG.debug(r)
        error = r.get('Error')
        errors = r.get('errors')
        r_data = r.get('data')
        links = r.get('links')

        if error:
            if error == 'Resource not found':
                # raise(TvdbResourceNotFound)
                # handle no data at a different level so it is more specific
                pass
            elif error.lower() == 'not authorized':
                # Note: Error string sometimes comes back as "Not authorized" or "Not Authorized"
                raise TvdbNotAuthorized()
            elif error.startswith(u"ID: ") and error.endswith("not found"):
                raise TvdbShowNotFound("%s" % error)
            else:
                raise TvdbError("%s" % error)

        if errors:
            if 'invalidLanguage' in errors:
                # raise(TvdbError(errors['invalidLanguage']))
                # invalidLanguage does not mean there is no data
                # there is just less data (missing translations)
                pass

        if data and isinstance(data, list):
            data.extend(r_data)
        else:
            data = r_data

        if links and links['next']:
            url = url.split('?')[0]
            _url = url + "?page=%s" % links['next']
            self._load_url(_url, data=data)

        return data

    def authorize(self):
        LOG.debug("auth")
        r = self.session.post(
            'https://api.thetvdb.com/login', json=self.config['auth_payload'], headers=self.headers
        )
        r_json = r.json()
        error = r_json.get('Error')
        if error:
            if error == 'Not Authorized':
                raise (TvdbNotAuthorized)
        token = r_json.get('token')
        self.headers['Authorization'] = "Bearer %s" % str(token)
        self.__authorized = True

    def _set_item(self, sid, seas, ep, attrib, value):
        """Creates a new episode, creating Show(), Season() and
        Episode()s as required. Called by _getShowData to populate show

        Since the nice-to-use tvdb[1][24]['name] interface
        makes it impossible to do tvdb[1][24]['name] = "name"
        and still be capable of checking if an episode exists
        so we can raise TvdbShowNotFound, we have a slightly
        less pretty method of setting items.. but since the API
        is supposed to be read-only, this is the best way to
        do it!
        The problem is that calling tvdb[1][24]['episodename'] = "name"
        calls __getitem__ on tvdb[1], there is no way to check if
        tvdb.__dict__ should have a key "1" before we auto-create it
        """
        if sid not in self.shows:
            self.shows[sid] = Show()
        if seas not in self.shows[sid]:
            self.shows[sid][seas] = Season(show=self.shows[sid])
        if ep not in self.shows[sid][seas]:
            self.shows[sid][seas][ep] = Episode(season=self.shows[sid][seas])
        self.shows[sid][seas][ep][attrib] = value

    def _set_show_data(self, sid, key, value):
        """Sets self.shows[sid] to a new Show instance, or sets the data
        """
        if sid not in self.shows:
            self.shows[sid] = Show()
        self.shows[sid].data[key] = value

    def search(self, series):
        """This searches TheTVDB.com for the series name
        and returns the result list
        """
        series = url_quote(series.encode("utf-8"))
        LOG.debug("Searching for show %s" % series)
        series_resp = self._load_url(self.config['url_getSeries'] % (series))
        if not series_resp:
            LOG.debug('Series result returned zero')
            raise TvdbShowNotFound(
                "Show-name search returned zero results (cannot find show on TVDB)"
            )

        all_series = []
        for series in series_resp:
            series['language'] = self.config['language']
            LOG.debug('Found series %(seriesName)s' % series)
            all_series.append(series)

        return all_series

    def _get_series(self, series):
        """This searches TheTVDB.com for the series name,
        If a custom_ui UI is configured, it uses this to select the correct
        series. If not, and interactive == True, ConsoleUI is used, if not
        BaseUI is used to select the first result.
        """
        all_series = self.search(series)

        if self.config['custom_ui'] is not None:
            LOG.debug("Using custom UI %s" % (repr(self.config['custom_ui'])))
            ui = self.config['custom_ui'](config=self.config)
        else:
            if not self.config['interactive']:
                LOG.debug('Auto-selecting first search result using BaseUI')
                ui = BaseUI(config=self.config)
            else:
                LOG.debug('Interactively selecting show using ConsoleUI')
                ui = ConsoleUI(config=self.config)

        return ui.select_series(all_series)

    def available_languages(self):
        """Returns a list of the available language abbreviations
        which can be used in Tvdb(language="...") etc
        """
        et = self._load_url("https://api.thetvdb.com/languages")
        languages = [x['abbreviation'] for x in et]
        return sorted(languages)

    def _parse_banners(self, sid):
        """Parses banners XML, from
        http://thetvdb.com/api/[APIKEY]/series/[SERIES ID]/banners.xml

        Banners are retrieved using t['show name]['_banners'], for example:

        >>> t = Tvdb(banners = True)
        >>> t['scrubs']['_banners'].keys()
        ['fanart', 'poster', 'seasonwide', 'season', 'series']
        >>> t['scrubs']['_banners']['poster']['680x1000'][35308]['_bannerpath']
        'http://thetvdb.com/banners/posters/76156-2.jpg'
        >>>

        Any key starting with an underscore has been processed (not the raw
        data from the XML)

        This interface will be improved in future versions.
        """
        LOG.debug('Getting season banners for %s' % (sid))
        banners_resp = self._load_url(self.config['url_seriesBanner'] % sid)
        banners = {}
        for cur_banner in banners_resp.keys():
            banners_info = self._load_url(self.config['url_seriesBannerInfo'] % (sid, cur_banner))
            for banner_info in banners_info:
                bid = banner_info.get('id')
                btype = banner_info.get('keyType')
                btype2 = banner_info.get('resolution')
                if btype is None or btype2 is None:
                    continue

                if btype not in banners:
                    banners[btype] = {}
                if btype2 not in banners[btype]:
                    banners[btype][btype2] = {}
                if bid not in banners[btype][btype2]:
                    banners[btype][btype2][bid] = {}

                banners[btype][btype2][bid]['bannerpath'] = banner_info['fileName']
                banners[btype][btype2][bid]['resolution'] = banner_info['resolution']
                banners[btype][btype2][bid]['subKey'] = banner_info['subKey']

                for k, v in list(banners[btype][btype2][bid].items()):
                    if k.endswith("path"):
                        new_key = "_%s" % k
                        LOG.debug("Transforming %s to %s" % (k, new_key))
                        new_url = self.config['url_artworkPrefix'] % v
                        banners[btype][btype2][bid][new_key] = new_url

            banners[btype]['raw'] = banners_info
            self._set_show_data(sid, "_banners", banners)

    def _parse_actors(self, sid):
        """Parsers actors XML, from
        http://thetvdb.com/api/[APIKEY]/series/[SERIES ID]/actors.xml

        Actors are retrieved using t['show name]['_actors'], for example:

        >>> t = Tvdb(actors = True)
        >>> actors = t['scrubs']['_actors']
        >>> type(actors)
        <class 'tvdb_api.Actors'>
        >>> type(actors[0])
        <class 'tvdb_api.Actor'>
        >>> actors[0]
        <Actor 'John C. McGinley'>
        >>> sorted(actors[0].keys())
        ['id', 'image', 'imageAdded', 'imageAuthor', 'lastUpdated', 'name', 'role',
        'seriesId', 'sortOrder']
        >>> actors[0]['name']
        'John C. McGinley'
        >>> actors[0]['image']
        'http://thetvdb.com/banners/actors/43638.jpg'

        Any key starting with an underscore has been processed (not the raw
        data from the XML)
        """
        LOG.debug("Getting actors for %s" % (sid))
        actors_resp = self._load_url(self.config['url_actorsInfo'] % (sid))

        cur_actors = Actors()
        for cur_actor_item in actors_resp:
            cur_actor = Actor()
            for tag, value in cur_actor_item.items():
                if value is not None:
                    if tag == "image":
                        value = self.config['url_artworkPrefix'] % (value)
                cur_actor[tag] = value
            cur_actors.append(cur_actor)
        self._set_show_data(sid, '_actors', cur_actors)

    def _get_show_data(self, sid, language):
        """Takes a series ID, gets the epInfo URL and parses the TVDB
        XML file into the shows dict in layout:
        shows[series_id][season_number][episode_number]
        """

        if self.config['language'] is None:
            LOG.debug('Config language is none, using show language')
            if language is None:
                raise TvdbError("config['language'] was None, this should not happen")
        else:
            LOG.debug(
                'Configured language %s override show language of %s'
                % (self.config['language'], language)
            )

        # Parse show information
        LOG.debug('Getting all series data for %s' % (sid))
        series_info_resp = self._load_url(self.config['url_seriesInfo'] % sid)
        for tag, value in series_info_resp.items():
            if value is not None:
                if tag in ['banner', 'fanart', 'poster']:
                    value = self.config['url_artworkPrefix'] % (value)

            self._set_show_data(sid, tag, value)
        # set language
        self._set_show_data(sid, 'language', self.config['language'])

        # Parse banners
        if self.config['banners_enabled']:
            self._parse_banners(sid)

        # Parse actors
        if self.config['actors_enabled']:
            self._parse_actors(sid)

        # Parse episode data
        LOG.debug('Getting all episodes of %s' % (sid))

        url = self.config['url_epInfo'] % sid

        eps_resp = self._load_url(url, language=language)

        for cur_ep in eps_resp:

            if self.config['dvdorder']:
                LOG.debug('Using DVD ordering.')
                use_dvd = (
                    cur_ep.get('dvdSeason') is not None
                    and cur_ep.get('dvdEpisodeNumber') is not None
                )
            else:
                use_dvd = False

            if use_dvd:
                elem_seasnum, elem_epno = cur_ep.get('dvdSeason'), cur_ep.get('dvdEpisodeNumber')
            else:
                elem_seasnum, elem_epno = cur_ep['airedSeason'], cur_ep['airedEpisodeNumber']

            if elem_seasnum is None or elem_epno is None:
                LOG.warning(
                    "An episode has incomplete season/episode number (season: %r, episode: %r)"
                    % (elem_seasnum, elem_epno)
                )
                # TODO: Should this happen?
                continue  # Skip to next episode

            seas_no = elem_seasnum
            ep_no = elem_epno

            for cur_item in cur_ep.keys():
                tag = cur_item
                value = cur_ep[cur_item]
                if value is not None:
                    if tag == 'filename':
                        value = self.config['url_artworkPrefix'] % (value)
                self._set_item(sid, seas_no, ep_no, tag, value)

    def _name_to_sid(self, name):
        """Takes show name, returns the correct series ID (if the show has
        already been grabbed), or grabs all episodes and returns
        the correct SID.
        """
        if name in self.corrections:
            LOG.debug('Correcting %s to %s' % (name, self.corrections[name]))
            sid = self.corrections[name]
        else:
            LOG.debug('Getting show %s' % name)
            selected_series = self._get_series(name)
            sid = selected_series['id']
            LOG.debug('Got %(seriesName)s, id %(id)s' % selected_series)

            self.corrections[name] = sid
            self._get_show_data(selected_series['id'], self.config['language'])

        return sid

    def __getitem__(self, key):
        """Handles tvdb_instance['seriesName'] calls.
        The dict index should be the show id
        """
        if isinstance(key, int):
            sid = key
        else:
            sid = self._name_to_sid(key)
            LOG.debug('Got series id %s' % sid)

        if sid not in self.shows:
            self._get_show_data(sid, self.config['language'])
        return self.shows[sid]

    def __repr__(self):
        return repr(self.shows)


def main():
    """Simple example of using tvdb_api - it just
    grabs an episode name interactively.
    """
    import logging

    logging.basicConfig(level=logging.DEBUG)

    tvdb_instance = Tvdb(interactive=False, cache=False)
    print(tvdb_instance['Scrubs']['seriesName'])
    print(tvdb_instance['Scrubs'][1][4]['episodename'])


if __name__ == '__main__':
    main()
