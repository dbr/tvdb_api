#!/usr/bin/env python
#encoding:utf-8
#author:dbr/Ben
#project:tvdb_api
#repository:http://github.com/dbr/tvdb_api
#license:unlicense (http://unlicense.org/)

"""Unittests for tvdb_api
"""

import os
import sys
import datetime
import pytest

# Force parent directory onto path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tvdb_api
from tvdb_api import (tvdb_shownotfound, tvdb_seasonnotfound,
                      tvdb_episodenotfound, tvdb_attributenotfound)


class TestTvdbBasic:
    # Used to store the cached instance of Tvdb()
    t = None

    @classmethod
    def setup_class(cls):
        if cls.t is None:
            cls.t = tvdb_api.Tvdb(cache=True, banners=False)

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
        assert len([season for season in self.t['Life on Mars']]) == 2

    def test_season_iter(self):
        """Iterating over a show returns episodes
        """
        assert len([episode for episode in self.t['Life on Mars'][1]]) == 8

    def test_get_episode_overview(self):
        """Checks episode overview is retrieved correctly.
        """
        assert self.t['Battlestar Galactica (2003)'][1][6]['overview'].startswith('When a new copy of Doral, a Cylon who had been previously') == True

    def test_get_parent(self):
        """Check accessing series from episode instance
        """
        show = self.t['Battlestar Galactica (2003)']
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
            cls.t = tvdb_api.Tvdb(cache=True, banners=False)

    def test_seasonnotfound(self):
        """Checks exception is thrown when season doesn't exist.
        """
        with pytest.raises(tvdb_seasonnotfound):
            self.t['CNNNN'][10]

    def test_shownotfound(self):
        """Checks exception is thrown when episode doesn't exist.
        """
        with pytest.raises(tvdb_shownotfound):
            self.t['the fake show thingy']

    def test_shownotfound(self):
        """Checks exception is thrown when episode doesn't exist.
        """
        with pytest.raises(tvdb_shownotfound):
            self.t[999999999999999]

    def test_episodenotfound(self):
        """Checks exception is raised for non-existent episode
        """
        with pytest.raises(tvdb_episodenotfound):
            self.t['Scrubs'][1][30]

    def test_attributenamenotfound(self):
        """Checks exception is thrown for if an attribute isn't found.
        """
        with pytest.raises(tvdb_attributenotfound):
            self.t['CNNNN'][1][6]['afakeattributething']
            self.t['CNNNN']['afakeattributething']


class TestTvdbSearch:
    # Used to store the cached instance of Tvdb()
    t = None

    @classmethod
    def setup_class(cls):
        if cls.t is None:
            cls.t = tvdb_api.Tvdb(cache=True, banners=False)

    def test_search_len(self):
        """There should be only one result matching
        """
        assert len(self.t['My Name Is Earl'].search('Faked My Own Death')) == 1

    def test_search_checkname(self):
        """Checks you can get the episode name of a search result
        """
        assert self.t['Scrubs'].search('my first')[0]['episodeName'] == 'My First Day'
        assert self.t['My Name Is Earl'].search('Faked My Own Death')[0]['episodeName'] == 'Faked My Own Death'

    def test_search_multiresults(self):
        """Checks search can return multiple results
        """
        assert (len(self.t['Scrubs'].search('my first')) >= 3) == True

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
        """Tests airedOn show method"""
        sr = self.t['Scrubs'].airedOn(datetime.date(2001, 10, 2))
        assert len(sr) == 1
        assert sr[0]['episodeName'] == u'My First Day'


class TestTvdbData:
    # Used to store the cached instance of Tvdb()
    t = None

    @classmethod
    def setup_class(cls):
        if cls.t is None:
            cls.t = tvdb_api.Tvdb(cache=True, banners=False)

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
            cls.t = tvdb_api.Tvdb(cache=True, banners=False)

    def test_repr_show(self):
        """Check repr() of Season
        """
        assert repr(self.t['CNNNN']).replace("u'", "'") == "<Show 'Chaser Non-Stop News Network (CNNNN)' (containing 3 seasons)>"

    def test_repr_season(self):
        """Check repr() of Season
        """
        assert repr(self.t['CNNNN'][1]) == "<Season instance (containing 9 episodes)>"

    def test_repr_episode(self):
        """Check repr() of Episode
        """
        assert repr(self.t['CNNNN'][1][1]).replace("u'", "'") == "<Episode 01x01 - 'Terror Alert'>"

    def test_have_all_languages(self):
        """Check valid_languages is up-to-date (compared to languages.xml)
        """
        et = self.t._getetsrc("https://api.thetvdb.com/languages")

        languages = [x['abbreviation'] for x in et]

        assert sorted(languages) == sorted(self.t.config['valid_languages'])


class TestTvdbLanguages:
    def test_episode_name_french(self):
        """Check episode data is in French (language="fr")
        """
        t = tvdb_api.Tvdb(cache = True, language = "fr")
        assert t['scrubs'][1][1]['episodeName'] == "Mon premier jour"
        assert t['scrubs']['overview'].startswith(u"J.D. est un jeune m\xe9decin qui d\xe9bute")

    def test_episode_name_spanish(self):
        """Check episode data is in Spanish (language="es")
        """
        t = tvdb_api.Tvdb(cache = True, language = "es")
        assert t['scrubs'][1][1]['episodeName'] == u'Mi primer día'
        assert t['scrubs']['overview'].startswith(u'Scrubs es una divertida comedia')

    def test_multilanguage_selection(self):
        """Check selected language is used
        """
        t_en = tvdb_api.Tvdb(
            cache=True,
            language = "en")
        t_it = tvdb_api.Tvdb(
            cache=True,
            language = "it")

        assert t_en['dexter'][1][2]['episodeName'] == "Crocodile"
        assert t_it['dexter'][1][2]['episodeName'] == "Lacrime di coccodrillo"


class TestTvdbUnicode:
    def test_search_in_chinese(self):
        """Check searching for show with language=zh returns Chinese seriesname
        """
        t = tvdb_api.Tvdb(cache=True, language="zh")
        show = t[u'T\xecnh Ng\u01b0\u1eddi Hi\u1ec7n \u0110\u1ea1i']
        assert type(show) == tvdb_api.Show
        assert show['seriesName'] == u'T\xecnh Ng\u01b0\u1eddi Hi\u1ec7n \u0110\u1ea1i'

    @pytest.mark.skip('Новое API не возвращает сразу все языки')
    def test_search_in_all_languages(self):
        """Check search_all_languages returns Chinese show, with language=en
        """
        t = tvdb_api.Tvdb(cache=True, search_all_languages=True, language="en")
        show = t[u'T\xecnh Ng\u01b0\u1eddi Hi\u1ec7n \u0110\u1ea1i']
        assert type(show) == tvdb_api.Show
        assert show['seriesName'] == u'Virtues Of Harmony II'


class TestTvdbBanners:
    # Used to store the cached instance of Tvdb()
    t = None

    @classmethod
    def setup_class(cls):
        if cls.t is None:
            cls.t = tvdb_api.Tvdb(cache=True, banners=True)

    def test_have_banners(self):
        """Check banners at least one banner is found
        """
        assert (len(self.t['scrubs']['_banners']) > 0) == True

    def test_banner_url(self):
        """Checks banner URLs start with http://
        """
        for banner_type, banner_data in self.t['scrubs']['_banners'].items():
            for res, res_data in banner_data.items():
                if res != 'raw':
                    for bid, banner_info in res_data.items():
                        assert banner_info['_bannerpath'].startswith("http://") == True

    @pytest.mark.skip('В новом API нет картинки у эпизода')
    def test_episode_image(self):
        """Checks episode 'filename' image is fully qualified URL
        """
        assert self.t['scrubs'][1][1]['filename'].startswith("http://") == True

    @pytest.mark.skip('В новом API у сериала кроме банера больше нет картинок')
    def test_show_artwork(self):
        """Checks various image URLs within season data are fully qualified
        """
        for key in ['banner', 'fanart', 'poster']:
            assert self.t['scrubs'][key].startswith("http://") == True


class TestTvdbActors:
    t = None

    @classmethod
    def setup_class(cls):
        if cls.t is None:
            cls.t = tvdb_api.Tvdb(cache=True, actors=True)

    def test_actors_is_correct_datatype(self):
        """Check show/_actors key exists and is correct type"""
        assert isinstance(self.t['scrubs']['_actors'], tvdb_api.Actors) == True

    def test_actors_has_actor(self):
        """Check show has at least one Actor
        """
        assert isinstance(self.t['scrubs']['_actors'][0], tvdb_api.Actor) == True

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
                assert actor['image'].startswith("http://") == True


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
        class Used(Exception):
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
            cls.t = tvdb_api.Tvdb(cache=True, actors=True)

    def test_actors_is_correct_datatype(self):
        """Check show/_actors key exists and is correct type"""
        assert self.t[76156]['seriesName'] == 'Scrubs'


class TestTvdbShowOrdering:
    # Used to store the cached instance of Tvdb()
    t_dvd = None
    t_air = None

    @classmethod
    def setup_class(cls):
        if cls.t_dvd is None:
            cls.t_dvd = tvdb_api.Tvdb(cache=True, dvdorder=True)

        if cls.t_air is None:
            cls.t_air = tvdb_api.Tvdb(cache=True)

    def test_ordering(self):
        """Test Tvdb.search method
        """
        assert u'The Train Job' == self.t_air['Firefly'][1][1]['episodeName']
        assert u'Serenity' == self.t_dvd['Firefly'][1][1]['episodeName']

        assert u'The Cat & the Claw (Part 1)' == self.t_air['Batman The Animated Series'][1][1]['episodeName']
        assert u'On Leather Wings' == self.t_dvd['Batman The Animated Series'][1][1]['episodeName']


class TestTvdbShowSearch:
    # Used to store the cached instance of Tvdb()
    t = None

    @classmethod
    def setup_class(cls):
        if cls.t is None:
            cls.t = tvdb_api.Tvdb(cache=True)

    def test_search(self):
        """Test Tvdb.search method
        """
        results = self.t.search("my name is earl")
        all_ids = [x['id'] for x in results]
        assert 75397 in all_ids


class TestTvdbAltNames:
    t = None

    @classmethod
    def setup_class(cls):
        if cls.t is None:
            cls.t = tvdb_api.Tvdb(cache=True, actors=True)

    def test_1(self):
        """Tests basic access of series name alias
        """
        results = self.t.search("Don't Trust the B---- in Apartment 23")
        series = results[0]
        assert 'Apartment 23' in series['aliases']

if __name__ == '__main__':
    pytest.main()
