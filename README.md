# nose2pytest
This package provides a script to make tests written for Nose usable inwith py.test without importing Nose.

This script automatically converts many of the basic nose.tools.assert_ functions to raw assert statements. 
To do this, run this script, giving it a folder to convert. Type nose2pytest -h for other options. The script 
has so far only been tested with Python 3.4. 

The script does not currently convert the following nose.tools items because they can easily be handled via
a global search-replace: 
- assert_raises: replace with "pytest.raises"
- assert_warns: replace with "pytest.warns"  

These are on the TODO list:
- assert_is_instance(a, b) -> assert isinstance(a, b)
- assert_count_equal(a,b) -> assert collections.Counter(a) == collections.Counter(b)
- assert_not_regex(a,b) -> assert not re.search(b, a)
- assert_regex(a,b) -> assert re.search(b, a)
- assert_almost_equals and assert_almost_equal(a, b, delta) -> abs(a - b) <= delta
- assert_almost_equals and assert_almost_equal(a, b, places) -> round(abs(b-a), places) == 0
- assert_almost_equals and assert_almost_equal(a, b) -> round(abs(b-a), 7) == 0
- assert_not_almost_equal and assert_not_almost_equals(a, b, delta) -> abs(a-b) > delta
- assert_not_almost_equal and assert_not_almost_equals(a, b, places) -> round(abs(b-a), places) != 0
- assert_not_almost_equal and assert_not_almost_equals(a, b) -> round(abs(b-a), 7) != 0

These are also on the TODO list but will probably be handled by making the assert_ functions available
from pytest (for example, pytest.assert_logs), in which ase a global search/replace of any of these 
assert_* functions by pytest.assert_* will be possible:
- assert_dict_contains_subset(a,b) -> assert set(b.keys()) >= a.keys() and {k: b[k] for k in a if k in b} == a
- assert_logs
- assert_raises_regex
- assert_raises_regexp  # deprecated
- assert_regexp_matches # deprecated
- assert_warns_regex
- @raises: could use the regular expression @raises\((.*)\) with the replacement @pytest.mark.xfail(raises=$1)
  but I prefer to convert test to use pytest.raises in test function body so there is no chance of having
  missed code (that gets added after the call that raises once you've forgotten that this code will never be
  reached!)

Once the above is handle, all "from nose.tools import ..." can be removed from your package test modules. 
