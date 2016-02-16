# nose2pytest
This package provides a script to convert Nose-based tests into py.test-based tests. Why? Because once a test 
suite is migrated from Nose to py.test, old code remains that uses `nose.tools.assert_*` functions and hence contains
Nose imports. Although new test code can be written in terms of raw (i.e. builtin) assertion statements, 
you don't want to 
carry more legacy than necessary, so if there is a way of converting Python code like `assert_greater(a, b)`
into `assert a > b`, so that legacy imports can be removed, why not do it? I prefer this to the
alternative approach of re-implementing the `assert_*` functions myself and replacing `from nose.tools` by 
`from mytestutils`: using raw assertions is more explicit and it's less to remember.
Also developers tend to copy code so if test code uses `assert_*` functions then new test code is likely going
to use it too. 

It turns out that this is largely possible, thanks to Python std lib's lib2to3 which, ironically, was 
developed for an entirely different purpose but has the same requirement: re-write code while maintaining 
spaces and comments. 

So this script automatically converts many of the basic `nose.tools.assert_*` functions to raw assert statements. 
To do this, run this script, giving it a folder to convert. Type `nose2pytest -h` for other options. The script 
has so far only been tested with Python 3.4, on Windows 7 Pro 64. 

The script only converts `nose.tools.assert_*` functions that I use in my code, but if you 
extend `nose2pytest` with a fixer that covers the missing cases, you are more than welcome 
to send a pull request. The missing ones can be grouped into several categories: 

1. Those that can be handled via a global search-replace, so a fixer is probably overkill: 
    - assert_raises: replace with "pytest.raises"
    - assert_warns: replace with "pytest.warns"
2. Those than could easily be handled with additional fixers:
    - assert_is_instance(a, b) -> assert isinstance(a, b)
    - assert_count_equal(a,b) -> assert collections.Counter(a) == collections.Counter(b)
    - assert_not_regex(a,b) -> assert not re.search(b, a)
    - assert_regex(a,b) -> assert re.search(b, a)
    - assert_almost_equals and assert_almost_equal(a, b, delta) -> abs(a - b) <= delta
    - assert_not_almost_equal and assert_not_almost_equals(a, b, delta) -> abs(a-b) > delta
3. Those that could be handled via fixers but the readability might be decreased, so it would likely be
   better to stick with utility functions, perhaps provided via a py.test plugin: 
    - assert_almost_equals and assert_almost_equal(a, b, places) -> round(abs(b-a), places) == 0
    - assert_almost_equals and assert_almost_equal(a, b) -> round(abs(b-a), 7) == 0
    - assert_not_almost_equal and assert_not_almost_equals(a, b, places) -> round(abs(b-a), places) != 0
    - assert_not_almost_equal and assert_not_almost_equals(a, b) -> round(abs(b-a), 7) != 0
    - assert_dict_contains_subset(a,b) -> assert set(b.keys()) >= a.keys() and {k: b[k] for k in a if k in b} == a
4. Those that propably could not be handled via a rewrite, i.e. they would likely have to be utility functions:
    - assert_logs
    - assert_raises_regex
    - assert_raises_regexp  # deprecated
    - assert_regexp_matches # deprecated
    - assert_warns_regex
    - @raises: could use the regular expression @raises\((.*)\) with the replacement @pytest.mark.xfail(raises=$1)
      but I prefer to convert test to use pytest.raises in test function body so there is no chance of having
      missed code (that gets added after the call that raises once you've forgotten that this code will never be
      reached!)

