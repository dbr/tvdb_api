# `tvdb_api` release procedure

1. Ensure CHANGELOG is up to date
2. Ensure tests are passing (CI and run again locally)
3. Verify settings in `setup.py` (e.g supported Python versions)
4. Bump version in setup.py and `tvdb_api.py`
5. Bump version/release date in CHANGELOG
6. Push changes to git
7. `python setup.py sdist upload`
8. Tag change, `git tag -a 0.0etc`
9. Push tag, `git push --tags`
10. Verify https://pypi.org/project/tvdb_api/
11. Verify via virtual env

        mkvirtualenv tvdbtest
        pip install tvdb_api
        python -c 'import tvdb_api; t = tvdb_api.Tvdb(); print t["scrubs"][1][2]'
        deactivate
        rmvirtualenv tvdbtest
