#!/usr/bin/env python
# encoding:utf-8

# author:dbr/Ben
# project:tvdb_api
# repository:http://github.com/dbr/tvdb_api
# license:unlicense (http://unlicense.org/)

"""Unittests for tvdb_api
"""

import os
import sys
import datetime
import unittest.mock

import pytest
import requests_cache.backends
import requests_cache.backends.base

# Force parent directory onto path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tvdb_api
from tvdb_api import (
    TvdbShowNotFound,
    TvdbSeasonNotFound,
    TvdbEpisodeNotFound,
    TvdbAttributeNotFound,
)


def get_test_cache_session():
    here = os.path.dirname(os.path.abspath(__file__))
    cacher = requests_cache.FileCache(
        cache_name=os.path.join(here, "http_cache"),
        serializer='json',
    )
    sess = requests_cache.CachedSession(
        backend=cacher,
        serializer='json',
        include_get_headers=True,
        allowable_codes=(200, 404),
        match_headers=['Accept-Language'],
    )
    return sess


class TestTvdbBasic:
    # Used to store the cached instance of Tvdb()
    t = None

    @classmethod
    def setup_class(cls):
        if cls.t is None:
            cls.t = tvdb_api.Tvdb(cache=get_test_cache_session(), banners=False)

    def test_different_case(self):
        """Checks the auto-correction of show names is working.
        It should correct the weirdly capitalised 'sCruBs' to 'Scrubs'
        """
        assert self.t['scrubs'][1][4]['episodeName'] == 'My Old Lady'
        assert self.t['sCruBs']['seriesName'] == 'Scrubs'

    def test_spaces(self):
        """Checks shownames with spaces
        """
        assert self.t['My Name Is Earl']['seriesName'] == 'My Name Is Earl'
        assert self.t['My Name Is Earl'][1][4]['episodeName'] == 'Faked My Own Death'

    def test_numeric(self):
        """Checks numeric show names
        """
        assert self.t['24'][2][20]['episodeName'] == 'Day 2: 3:00 A.M. - 4:00 A.M.'
        assert self.t['24']['seriesName'] == '24'

    def test_show_iter(self):
        """Iterating over a show returns each seasons
        """
        assert len([season for season in self.t['scrubs']]) == 10

    def test_season_iter(self):
        """Iterating over a show returns episodes
        """
        assert len([episode for episode in self.t['scrubs'][1]]) == 24

    def test_get_episode_overview(self):
        """Checks episode overview is retrieved correctly.
        """
        assert self.t['Scrubs'][1][6]['overview'].startswith(
            'Dr. Cox is still facing the threat of suspension'
        )

        try:
            self.t['Scrubs']['something nonsensical']
        except TvdbAttributeNotFound:
            pass  # good
        else:
            raise AssertionError("Expected attribute error")

    def test_get_parent(self):
        """Check accessing series from episode instance
        """
        show = self.t['Scrubs']
        season = show[1]
        episode = show[1][1]

        assert season.show == show
        assert episode.season == season
        assert episode.season.show == show

    def test_no_season(self):
        show = self.t['Katekyo Hitman Reborn']
        print(tvdb_api)
        print(show[1][1])


class TestTvdbErrors:
    t = None

    @classmethod
    def setup_class(cls):
        if cls.t is None:
            cls.t = tvdb_api.Tvdb(cache=get_test_cache_session(), banners=False)

    def test_seasonnotfound(self):
        """Checks exception is thrown when season doesn't exist.
        """
        with pytest.raises(TvdbSeasonNotFound):
            self.t['Scrubs'][42]

    def test_shownotfound(self):
        """Checks exception is thrown when episode doesn't exist.
        """
        with pytest.raises(TvdbShowNotFound):
            self.t['the fake show thingy']

    def test_shownotfound_by_id(self):
        """Checks exception is thrown when episode doesn't exist.
        """
        with pytest.raises(TvdbShowNotFound):
            self.t[999999999999999999999999]

    def test_episodenotfound(self):
        """Checks exception is raised for non-existent episode
        """
        with pytest.raises(TvdbEpisodeNotFound):
            self.t['Scrubs'][1][30]

    def test_attributenamenotfound(self):
        """Checks exception is thrown for if an attribute isn't found.
        """
        with pytest.raises(TvdbAttributeNotFound):
            self.t['Scrubs'][1][6]['afakeattributething']
            self.t['Scrubs']['afakeattributething']


class TestTvdbSearch:
    # Used to store the cached instance of Tvdb()
    t = None

    @classmethod
    def setup_class(cls):
        if cls.t is None:
            cls.t = tvdb_api.Tvdb(cache=get_test_cache_session(), banners=False)

    def test_search_len(self):
        """There should be only one result matching
        """
        assert len(self.t['My Name Is Earl'].search('Faked My Own Death')) == 1

    def test_search_checkname(self):
        """Checks you can get the episode name of a search result
        """
        assert self.t['Scrubs'].search('my first')[0]['episodeName'] == 'My First Day'
        assert (
            self.t['My Name Is Earl'].search('Faked My Own Death')[0]['episodeName']
            == 'Faked My Own Death'
        )

    def test_search_multiresults(self):
        """Checks search can return multiple results
        """
        assert len(self.t['Scrubs'].search('my first')) >= 3

    def test_search_no_params_error(self):
        """Checks not supplying search info raises TypeError"""
        with pytest.raises(TypeError):
            self.t['Scrubs'].search()

    def test_search_season(self):
        """Checks the searching of a single season"""
        assert len(self.t['Scrubs'][1].search("First")) == 3

    def test_search_show(self):
        """Checks the searching of an entire show"""
        assert len(self.t['CNNNN'].search('CNNNN', key='episodeName')) == 3

    def test_aired_on(self):
        """Tests aired_on show method"""
        sr = self.t['Scrubs'].aired_on(datetime.date(2001, 10, 2))
        assert len(sr) == 1
        assert sr[0]['episodeName'] == 'My First Day'

        try:
            sr = self.t['Scrubs'].aired_on(datetime.date(1801, 1, 1))
        except TvdbEpisodeNotFound:
            pass  # Good
        else:
            raise AssertionError("expected episode not found exception")


class TestTvdbData:
    # Used to store the cached instance of Tvdb()
    t = None

    @classmethod
    def setup_class(cls):
        if cls.t is None:
            cls.t = tvdb_api.Tvdb(cache=get_test_cache_session(), banners=False)

    def test_episode_data(self):
        """Check the firstaired value is retrieved
        """
        assert self.t['lost']['firstAired'] == '2004-09-22'


class TestTvdbMisc:
    # Used to store the cached instance of Tvdb()
    t = None

    @classmethod
    def setup_class(cls):
        if cls.t is None:
            cls.t = tvdb_api.Tvdb(cache=get_test_cache_session(), banners=False)

    def test_repr_show(self):
        """Check repr() of Season
        """
        assert (
            repr(self.t['CNNNN'])
            == "<Show 'Chaser Non-Stop News Network (CNNNN)' (containing 3 seasons)>"
        )

    def test_repr_season(self):
        """Check repr() of Season
        """
        assert repr(self.t['CNNNN'][1]) == "<Season instance (containing 9 episodes)>"

    def test_repr_episode(self):
        """Check repr() of Episode
        """
        assert repr(self.t['CNNNN'][1][1]) == "<Episode 01x01 - 'Terror Alert'>"

    def test_available_langs(self):
        """Check available_languages returns something sane looking
        """
        langs = self.t.available_languages()
        print(langs)
        assert "en" in langs


class TestTvdbLanguages:
    def test_episode_name_french(self):
        """Check episode data is in French (language="fr")
        """
        t = tvdb_api.Tvdb(cache=get_test_cache_session(), language="fr")
        assert t['scrubs'][1][1]['episodeName'] == "Mon premier jour"
        assert t['scrubs']['overview'].startswith(u"J.D. est un jeune m\xe9decin qui d\xe9bute")

    def test_episode_name_spanish(self):
        """Check episode data is in Spanish (language="es")
        """
        t = tvdb_api.Tvdb(cache=get_test_cache_session(), language="es")
        assert t['scrubs'][1][1]['episodeName'] == 'Mi primer día'
        assert t['scrubs']['overview'].startswith('Scrubs es una divertida comedia')

    def test_multilanguage_selection(self):
        """Check selected language is used
        """
        t_en = tvdb_api.Tvdb(cache=get_test_cache_session(), language="en")
        t_it = tvdb_api.Tvdb(cache=get_test_cache_session(), language="it")

        assert t_en['dexter'][1][2]['episodeName'] == "Crocodile"
        assert t_it['dexter'][1][2]['episodeName'] == "Lacrime di coccodrillo"


class TestTvdbUnicode:
    def test_search_in_chinese(self):
        """Check searching for show with language=zh returns Chinese seriesname
        """
        t = tvdb_api.Tvdb(cache=get_test_cache_session(), language="zh")
        show = t['T\xecnh Ng\u01b0\u1eddi Hi\u1ec7n \u0110\u1ea1i']
        assert type(show) == tvdb_api.Show
        assert show['seriesName'] == 'T\xecnh Ng\u01b0\u1eddi Hi\u1ec7n \u0110\u1ea1i'


class TestTvdbBanners:
    # Used to store the cached instance of Tvdb()
    t = None

    @classmethod
    def setup_class(cls):
        if cls.t is None:
            cls.t = tvdb_api.Tvdb(cache=get_test_cache_session(), banners=True)

    def test_have_banners(self):
        """Check banners at least one banner is found
        """
        assert len(self.t['scrubs']['_banners']) > 0

    def test_banner_url(self):
        """Checks banner URLs start with http://
        """
        for banner_type, banner_data in self.t['scrubs']['_banners'].items():
            for res, res_data in banner_data.items():
                if res != 'raw':
                    for bid, banner_info in res_data.items():
                        assert banner_info['_bannerpath'].startswith("http://")

    def test_episode_image(self):
        """Checks episode 'filename' image is fully qualified URL
        """
        assert self.t['scrubs'][1][1]['filename'].startswith("http://")

    def test_show_artwork(self):
        """Checks various image URLs within season data are fully qualified
        """
        for key in ['banner', 'fanart', 'poster']:
            assert self.t['scrubs'][key].startswith("http://")


class TestTvdbActors:
    t = None

    @classmethod
    def setup_class(cls):
        if cls.t is None:
            cls.t = tvdb_api.Tvdb(cache=get_test_cache_session(), actors=True)

    def test_actors_is_correct_datatype(self):
        """Check show/_actors key exists and is correct type"""
        assert isinstance(self.t['scrubs']['_actors'], tvdb_api.Actors)

    def test_actors_has_actor(self):
        """Check show has at least one Actor
        """
        assert isinstance(self.t['scrubs']['_actors'][0], tvdb_api.Actor)

    def test_actor_has_name(self):
        """Check first actor has a name"""
        names = [actor['name'] for actor in self.t['scrubs']['_actors']]

        assert u"Zach Braff" in names

    def test_actor_image_corrected(self):
        """Check image URL is fully qualified
        """
        for actor in self.t['scrubs']['_actors']:
            if actor['image'] is not None:
                # Actor's image can be None, it displays as the placeholder
                # image on thetvdb.com
                assert actor['image'].startswith("http://")


class TestTvdbDoctest:
    def test_doctest(self):
        """Check docstring examples works"""
        import doctest
        doctest.testmod(tvdb_api)


class TestTvdbCustomCaching:
    def test_true_false_string(self):
        """Tests setting cache to True/False/string

        Basic tests, only checking for errors
        """
        tvdb_api.Tvdb(cache=True)
        tvdb_api.Tvdb(cache=False)
        tvdb_api.Tvdb(cache="/tmp")

    def test_invalid_cache_option(self):
        """Tests setting cache to invalid value
        """

        try:
            tvdb_api.Tvdb(cache=2.3)
        except ValueError:
            pass
        else:
            pytest.fail("Expected ValueError from setting cache to float")

    def test_custom_request_session(self):
        from requests import Session as OriginalSession

        class Used(Exception):  # noqa: N818
            pass

        class CustomCacheForTest(OriginalSession):
            call_count = 0

            def request(self, *args, **kwargs):
                raise Used("Hurray")

        c = CustomCacheForTest()
        t = tvdb_api.Tvdb(cache=c)
        try:
            t['scrubs']
        except Used:
            pass
        else:
            pytest.fail("Did not use custom session")


class TestTvdbById:
    t = None

    @classmethod
    def setup_class(cls):
        if cls.t is None:
            cls.t = tvdb_api.Tvdb(cache=get_test_cache_session(), actors=True)

    def test_actors_is_correct_datatype(self):
        """Check show/_actors key exists and is correct type"""
        assert self.t[76156]['seriesName'] == 'Scrubs'


class TestTvdbShowOrdering:
    def test_ordering(self):
        """Test Tvdb.search method
        """
        t_dvd = tvdb_api.Tvdb(cache=get_test_cache_session(), dvdorder=True)
        t_air = tvdb_api.Tvdb(cache=get_test_cache_session())

        assert 'The Train Job' == t_air['Firefly'][1][1]['episodeName']
        assert 'Serenity' == t_dvd['Firefly'][1][1]['episodeName']

        assert (
            'The Cat and the Claw (1)' == t_air['Batman The Animated Series'][1][1]['episodeName']
        )
        assert 'On Leather Wings' == t_dvd['Batman The Animated Series'][1][1]['episodeName']


class TestTvdbShowSearch:
    # Used to store the cached instance of Tvdb()
    t = None

    @classmethod
    def setup_class(cls):
        if cls.t is None:
            cls.t = tvdb_api.Tvdb(cache=get_test_cache_session())

    def test_search(self):
        """Test Tvdb.search method
        """
        results = self.t.search("my name is earl")
        all_ids = [x['id'] for x in results]
        assert 75397 in all_ids

def raise_error(e):
    raise e

class TestConsoleUI:
    @unittest.mock.patch('builtins.input', lambda *args: '1')
    def test_first_option(self):
        t = tvdb_api.Tvdb(cache=get_test_cache_session(), custom_ui=tvdb_api.ConsoleUI)
        episode = t['scrubs'][1][2]
        assert episode['episodeName'] == 'My Mentor'

    @unittest.mock.patch('builtins.input', lambda *args: '2')
    def test_second_option(self):
        t = tvdb_api.Tvdb(cache=get_test_cache_session(), custom_ui=tvdb_api.ConsoleUI)
        episode = t['scrubs'][1][2]
        # Test second result is anything but the first option (not being specific to avoid sporadic test failures if results change order)
        assert episode['episodeName'] != 'My Mentor'

    def test_select_first(self):
        t = tvdb_api.Tvdb(cache=get_test_cache_session(), custom_ui=tvdb_api.ConsoleUI, select_first=True)
        episode = t['scrubs'][1][2]
        assert episode['episodeName'] == 'My Mentor'

    @unittest.mock.patch('builtins.input', lambda *args: 'asdfasdf')
    def test_first_option(self):
        t = tvdb_api.Tvdb(cache=get_test_cache_session(), custom_ui=tvdb_api.ConsoleUI)
        episode = t['cnnnn'][1][2]
        assert episode['episodeName'] == 'Terrorthon'

    @unittest.mock.patch('builtins.input', lambda *args: raise_error(KeyboardInterrupt("Stopit")))
    def test_select_interrupted(self):
        t = tvdb_api.Tvdb(cache=get_test_cache_session(), custom_ui=tvdb_api.ConsoleUI)
        try:
            episode = t['scrubs'][1][2]
        except tvdb_api.TvdbUserAbort as e:
            pass
        else:
            # Expected error
            assert False

    @unittest.mock.patch('builtins.input', lambda *args: raise_error(EOFError()))
    def test_select_error(self):
        t = tvdb_api.Tvdb(cache=get_test_cache_session(), custom_ui=tvdb_api.ConsoleUI)
        try:
            episode = t['scrubs'][1][2]
        except tvdb_api.TvdbUserAbort as e:
            pass
        else:
            # Expected error
            assert False


class TestTvdbAltNames:
    t = None

    @classmethod
    def setup_class(cls):
        if cls.t is None:
            cls.t = tvdb_api.Tvdb(cache=get_test_cache_session(), actors=True)

    def test_1(self):
        """Tests basic access of series name alias
        """
        results = self.t.search("Don't Trust the B---- in Apartment 23")
        series = results[0]
        assert 'Apartment 23' in series['aliases']


if __name__ == '__main__':
    pytest.main()
