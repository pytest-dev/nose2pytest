# nose2pytest
Scripts to convert Python Nose tests to PyTest (convert assert_ calls to regular assertions)

Convert Python nose assertions to pytest assertions.

This script automatically converts the basic assert_ functions to raw assert statements. The following functions
must currently be done maunally via search-replace:
- @raises: could use the regular expression @raises\((.*)\) with the replacement @pytest.mark.xfail(raises=$1)
  but I prefer to convert test to use pytest.raises in test function body so there is no chance of having
  missed code (that gets added after the call that raises once you've forgotten that this code will never be
  reached!)
- assert_is_instance: replace with "assert isinstance"
- assert_raises: replace with "pytest.raises"
- assert_warns: replace with "pytest.warns"

These are on the todo list:
- assert_count_equal(a,b) -> assert collections.Counter(a) == collections.Counter(b)
- assert_not_regex(a,b) -> assert not re.search(b, a)
- assert_regex(a,b) -> assert re.search(b, a)
- assert_almost_equals and assert_almost_equal(a, b, delta) -> abs(a - b) <= delta
- assert_almost_equals and assert_almost_equal(a, b, places) -> round(abs(b-a), places) == 0
- assert_almost_equals and assert_almost_equal(a, b) -> round(abs(b-a), 7) == 0
- assert_not_almost_equal and assert_not_almost_equals(a, b, delta) -> abs(a-b) > delta
- assert_not_almost_equal and assert_not_almost_equals(a, b, places) -> round(abs(b-a), places) != 0
- assert_not_almost_equal and assert_not_almost_equals(a, b) -> round(abs(b-a), 7) != 0

The remaining should be converted by re-implementing lightweight version in pytest and importing from there,
in which case a search-replace of nose.tools to pytest would be sufficient:
- assert_dict_contains_subset(a,b) -> assert set(b.keys()) >= a.keys() and {k: b[k] for k in a if k in b} == a
- assert_logs
- assert_raises_regex
- assert_raises_regexp  # deprecated
- assert_regexp_matches # deprecated
- assert_warns_regex
