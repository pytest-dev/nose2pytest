# nose2pytest
This package provides a Python script to convert Nose-based tests into py.test-based tests. 

Motivation: once a test suite is migrated from Nose to py.test, old test code remains that uses `nose.tools.assert_*` 
functions and hence contains Nose imports. Although new test code can be written in terms of raw (i.e. builtin) 
assertion statements to take advantage of py.test assertion introspection, why burden yourself with legacy (Nose)
test functions if it is not necessary? Developers tend to copy code so if test code uses `assert_*` functions then 
new test code is likely going to use it too, and one of the benefits of using py.test is diminished.

It turns out that this is largely possible, thanks to Python standard lib's lib2to3. This library, although it was 
developed for the purpose of converting Python 2.7 code into Python 3 code, contains code matching, transformation, 
and generation routines that preserve formatting and comments. For example, it makes it easy to re-write modules
that use `assert_greater(a, b)`, with arbitrarily complex Python expressions for a and b, into a module that 
uses `assert a > b`. 

So the nose2pytest script automatically converts many of the basic `nose.tools.assert_*` functions to raw assert 
statements:

- assert_equal, assert_equals
- assert_greater, assert_less, ...
- assert_is_none, assert_is_not_none
- assert_set_equal, ...
- etc

To do this, run this script, giving it a folder to convert, it will find all .py files in the folder tree and 
will overwrite the original (since we all work with version-control this is easiest). Then do a diff before 
committing, to verify that all conversions have succeeded. Type `nose2pytest -h` for other options.

The script has so far only been tested with Python 3.4, on Windows 7 Pro 64. 

Note that not every `nose.tools.assert_*` function can be converted by nose2pytest because some functions don't 
have a straightforward assertion statement equivalent. The missing ones can be grouped into several categories: 

1. Those that can be handled via a global search-replace, so a fixer was overkill: 
    - `assert_raises`: replace with `pytest.raises`
    - `assert_warns`: replace with `pytest.warns`
2. Those than could easily be handled with additional fixers, but not done yet:
    - `assert_almost_equals` and `assert_almost_equal(a, b, delta) -> abs(a - b) <= delta`
    - `assert_not_almost_equal` and `assert_not_almost_equals(a, b, delta) -> abs(a-b) > delta`
3. Those that could be handled via fixers but the readability might be decreased, so it would likely be
   better to stick with utility functions, perhaps provided via a py.test plugin: 
    - `assert_almost_equals` and `assert_almost_equal(a, b, places) -> round(abs(b-a), places) == 0`
    - `assert_almost_equals` and `assert_almost_equal(a, b) -> round(abs(b-a), 7) == 0`
    - `assert_not_almost_equal` and `assert_not_almost_equals(a, b, places) -> round(abs(b-a), places) != 0`
    - `assert_not_almost_equal` and `assert_not_almost_equals(a, b) -> round(abs(b-a), 7) != 0`
    - `assert_dict_contains_subset(a,b) -> assert set(b.keys()) >= a.keys() and {k: b[k] for k in a if k in b} == a`
4. Those that propably could not be handled via a rewrite, i.e. they would likely have to be utility functions:
    - `assert_logs`
    - `assert_raises_regex`
    - `assert_raises_regexp`  # deprecated
    - `assert_regexp_matches` # deprecated
    - `assert_warns_regex`
    - `@raises`: could use the regular expression `@raises\((.*)\)` with the replacement `@pytest.mark.xfail(raises=$1)`
      but I prefer to convert test to use `pytest.raises` in test function body so there is no chance of having
      missed code (that gets added after the call that raises once you've forgotten that this code will never be
      reached!)

Contributions to address the above limitations are welcome, just send me a pull request.
 
Note that there are a couple of tricky aspects to this: 

- multiline arguments: Python handles multiline expressions when they are surrounded by parentheses, brackets 
  or braces, but not otherwise. For example if 
  ```python
  assert_func(long_a +
              long_b)
  ``` 
  gets converted to 
  ```python
  assert long_a +
            long_b
  ``` 
  you get a syntax error when the resulting module gets loaded. However, 
  ```python
  assert_func(long_a + (long_b +
                        long_c))
  ``` 
  is fine. So nose2pytest checks each argument expression (such as `long_a +\n long_b`) to see if it has 
  newlines that would cause an invalid syntax, and if so, wraps it in parentheses. 
  
- operator precedence: Python assigns a precedence to each operator; operators that are on the same level
  of precedence (like the comparison operators ==, >=, !=, etc) are executed in sequence. This is a problem 
  for a two-argument assertion function being converted to an assertion statement using an operator, like:
  ```python
  assert_func(a != b, a <= c)
  ``` 
  which would get translated to 
  ```python
  assert a != b == a <= c
  ```
  Even in the off-chance this does what the original
  code did, it is unmaintainable! To keep it simple, if either argument is "composite" (consists of multiple
  smaller pieces), it is wrapped with parentheses. The above would get converted to:
  ```python
  assert (a != b) == (a <= c)
  ```
  if assert_func is assert_equal. 
