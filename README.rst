.. image:: https://badge.fury.io/py/nose2pytest.svg
    :target: https://badge.fury.io/py/nose2pytest
.. image:: https://github.com/pytest-dev/nose2pytest/workflows/Test/badge.svg
    :target: https://github.com/pytest-dev/nose2pytest/actions


.. contents::


Overview
------------

This package provides a Python script and pytest plugin to help convert Nose-based tests into pytest-based
tests. Specifically, the script transforms ``nose.tools.assert_*`` function calls into raw assert statements, 
while preserving format of original arguments as much as possible. For example, the script:

.. code-block:: python

  assert_true(a, msg)
  assert_greater(a, b, msg)
  
gets converted to:

.. code-block:: python

  assert a, msg
  assert a > b, msg

A small subset of ``nose.tools.assert_*`` function calls are not 
transformed because there is no raw assert statement equivalent, or the equivalent would be hard to 
maintain. They are provided as functions in the pytest namespace via pytest's plugin system.


Installation
-------------

From a command shell run ::

  pip install nose2pytest

This puts an executable file in ``<python-root>/Scripts`` with *python-root* being the root folder of the 
Python installation from which ``pip`` was run.


Running
------------

From a command shell, ::

  nose2pytest path/to/dir/with/python_files
  
This will find all ``.py`` files in the folder tree starting at ``path/to/dir/with/python_files`` and 
overwrite the original (assuming most users will be running this on a version-controlled code base, this is
almost always what would be most convenient). Type ``nose2pytest -h`` for other options, such as ``-v``. 


Motivation
------------

I have used Nose for years and it is a great tool. However, to get good test failure diagnostics with Nose you 
ought to use the ``assert_*()`` functions from ``nose.tools``. Although they provide very good diagnostics, they 
are not as convenient to use as raw assertions, since you have to decide before hand what type of assertion you 
are going to write: an identity comparison to None, a truth check, a falseness check, an identity comparison to another 
object, etc. Just being able to write a raw assertion, and still get good diagnostics on failure as done by 
pytest, is really nice. This is a main reason for using pytest for me. Another reason is the design of fixtures
in pytest.

Switching an existing test suite from Nose to pytest is feasible even without nose2pytest, as it requires
relatively little work: *relatively* as in, you will probably only need a few modifications, all achievable 
manually, to get the same test coverage and results. A few gotchas: 
  
- test classes that have ``__init__`` will be ignored, those will have to be moved (usually, into class's 
  ``setup_class()``)
- the ``setup.cfg`` may have to be edited since test discovery rules are slightly more strict with pytest
- the order of tests may be different, but in general that should not matter
- all test modules are imported up-front, so some test modules may need adjustment such as moving some 
  code from the top of the test module into its ``setup_module()`` 
    
Once the above has been done to an existing code base, you don't really have to do anything else. However, your test 
suite now has an additional third-party test dependency (Nose), just because of those ``assert_*`` functions used all 
over the place. Moreover, there is no longer one obvious way to do things in your test suite: existing test code 
uses ``nose.tools.assert_*`` functions, yet with pytest you can use raw assertions. If you add tests, which of
these two approaches should a developer use? If you modify existing tests, should new assertions use raw assert? 
Should the remaining test method, test class, or test module be updated? A test module can contain hundreds of 
calls to ``nose.tools.assert_*`` functions, is a developer to manually go through each one to convert it? Painful and 
error prone, in general not feasible to do manually. 

This is why I developed nose2pytest: I wanted to migrate my pypubsub project's test suite from Nose to pytest,
but also have only pytest as a dependency, and have one obvious way to write assertions in the test suite.
  

Requirements
-------------

I expect nose2pytest script to run with Python >= 3.4, to correctly convert Python test suite >= 2.7, on any 
OS supported by a version of python that has lib2to3 compatible with Python 3.4's lib2to3. I expect it to 
succeed even with quite old versions of Nose (even prior to 1.0 which came out ca. 2010), and with the new 
Nose2 test driver. 

Note however that I have run the script only with Python 3.4, to convert Python 3.4 test suites based on 
Nose 1.3.7 on Windows 7 Pro 64. If you have successfully used nose2pytest with other combinations, please 
kindly let me know (via github). 

The pytest package namespace will be extended with ``assert_`` functions that are not converted by the script
only if, err, you have pytest installed!


Status
------------------------------

The package has been used on over 5000 ``assert_*()`` function calls, among which the pypubsub test suite.
I consider it stable, but I have only used it on my code, and code by a few other developers. Feedback on 
results of conversions would be most appreciated (such as version information and number of assert statements
converted).
 
The following conversions have been implemented:

============================================ =================================================================
Function                                     Statement
============================================ =================================================================
assert_true(a[, msg])                        assert a[, msg]
assert_false(a[, msg])                       assert not a[, msg]
assert_is_none(a[, msg])                     assert a is None[, msg]
assert_is_not_none(a[, msg])                 assert a is not None[, msg]
-------------------------------------------- -----------------------------------------------------------------
assert_equal(a,b[, msg])                     assert a == b[, msg]
assert_equals(a,b[, msg])                    assert a == b[, msg]
assert_not_equal(a,b[, msg])                 assert a != b[, msg]
assert_not_equals(a,b[, msg])                assert a != b[, msg]
assert_list_equal(a,b[, msg])                assert a == b[, msg]
assert_dict_equal(a,b[, msg])                assert a == b[, msg]
assert_set_equal(a,b[, msg])                 assert a == b[, msg]
assert_sequence_equal(a,b[, msg])            assert a == b[, msg]
assert_tuple_equal(a,b[, msg])               assert a == b[, msg]
assert_multi_line_equal(a,b[, msg])          assert a == b[, msg]
assert_greater(a,b[, msg])                   assert a > b[, msg]
assert_greater_equal(a,b[, msg])             assert a >= b[, msg]
assert_less(a,b[, msg])                      assert a < b[, msg]
assert_less_equal(a,b[, msg])                assert a <= b[, msg]
assert_in(a,b[, msg])                        assert a in b[, msg]
assert_not_in(a,b[, msg])                    assert a not in b[, msg]
assert_is(a,b[, msg])                        assert a is b[, msg]
assert_is_not(a,b[, msg])                    assert a is not b[, msg]
-------------------------------------------- -----------------------------------------------------------------
assert_is_instance(a,b[, msg])               assert isinstance(a, b)[, msg]
assert_count_equal(a,b[, msg])               assert collections.Counter(a) == collections.Counter(b)[, msg]
assert_not_regex(a,b[, msg])                 assert not re.search(b, a)[, msg]
assert_regex(a,b[, msg])                     assert re.search(b, a)[, msg]
-------------------------------------------- -----------------------------------------------------------------
assert_almost_equal(a,b, delta[, msg])       assert abs(a - b) <= delta[, msg]
assert_almost_equals(a,b, delta[, msg])      assert abs(a - b) <= delta[, msg]
assert_not_almost_equal(a,b, delta[, msg])   assert abs(a - b) > delta[, msg]
assert_not_almost_equals(a,b, delta[, msg])  assert abs(a - b) > delta[, msg]
============================================ =================================================================

The script adds parentheses around ``a`` and/or ``b`` if operator precedence would change the interpretation of the 
expression or involves newline. For example:

.. code-block:: python

  assert_true(some-long-expression-a in 
              some-long-expression-b, msg)
  assert_equal(a == b, b == c), msg
    
gets converted to:

.. code-block:: python

  assert (some-long-expression-a in 
              some-long-expression-b), msg
  assert (a == b) == (b == c), msg

Not every ``assert_*`` function from ``nose.tools`` is converted by nose2pytest: 

1. Some Nose functions can be handled via a global search-replace, so a fixer was not a necessity: 

   - ``assert_raises``: replace with ``pytest.raises``
   - ``assert_warns``: replace with ``pytest.warns``
     
2. Some Nose functions could be transformed but the readability would be decreased: 
   
   - ``assert_almost_equal(a, b, places)`` -> ``assert round(abs(b-a), places) == 0``
   - ``assert_almost_equal(a, b)`` -> ``assert round(abs(b-a), 7) == 0``
   - ``assert_not_almost_equal(a, b, places)`` -> ``assert round(abs(b-a), places) != 0``
   - ``assert_not_almost_equal(a, b)`` -> ``assert round(abs(b-a), 7) != 0``
   - ``assert_dict_contains_subset(a,b)`` -> ``assert set(b.keys()) >= a.keys() and {k: b[k] for k in a if k in b} == a``
    
   The nose2pytest distribution contains a module, ``assert_tools.py`` which defines these utility functions to 
   contain the equivalent raw assert statement. Copy the module into your test folder or into the pytest package 
   and change your test code's ``from nose.tools import ...`` statements accordingly. pytest introspection will
   provide error information on assertion failure.
    
3. Some Nose functions don't have a one-line assert statement equivalent, they have to remain utility functions:

   - ``assert_raises_regex``
   - ``assert_raises_regexp``  # deprecated by Nose
   - ``assert_regexp_matches`` # deprecated by Nose
   - ``assert_warns_regex``
   
   These functions are available in ``assert_tools.py`` of nose2pytest distribution, and are imported as 
   is from ``unittest.TestCase`` (but renamed as per Nose). Copy the module into your test folder or into 
   the pytest package and change your test code's ``from nose.tools import ...`` statements accordingly. 
    
4. Some Nose functions simply weren't on my radar; for example I just noticed for the first time that there 
   is a ``nose.tools.ok_()`` function which is the same as ``assert_equal``. Feel free to contribute via email
   or pull requests. 


Limitations
------------

- The script does not convert ``nose.tools.assert_`` import statements as there are too many possibilities. 
  Should ``from nose.tools import ...`` be changed to ``from pytest import ...``, and the implemented 
  conversions removed? Should an ``import pytest`` statement be added, and if so, where? If it is added after
  the line that had the ``nose.tools`` import, is the previous line really needed? Indeed the ``assert_``
  functions added in the ``pytest`` namespace could be accessed via ``pytest.assert_``, in which case the 
  script should prepend ``pytest.`` and remove the ``from nose.tools import ...`` entirely. Too many options, 
  and you can fairly easily handle this via a global regexp search/replace.

- Similarly, statements of the form ``nose.tools.assert_`` are not converted: this would require some form 
  of semantic analysis of each call to a function, because any of the following are possible:

  .. code-block:: python

    import nose.tools as nt

    nt.assert_true(...)

    nt2 = nt
    nt2.assert_true(...)
    nt2.assert_true(...)

    import bogo.assert_true
    bogo.assert_true(...)  # should this one be converted? 
  
  The possiblities are endless so supporting this would require such a large amount of time that I 
  do not have. As with other limitations in this section

- Nose functions that can be used as context managers can obviously not be converted to raw assertions. 
  However, there is currently no way of preventing nose2pytest from converting Nose functions used this way. 
  You will have to manually fix.
  
- The lib2to3 package that nose2pytest relies on assumes python 2.7 syntax as input. The only issue that 
  this has caused so far on code base of 20k lines of python 3.4 *test* code (i.e. the source code does not 
  matter, as none of the test code, such as import statements, is actually run) are keywords like ``exec`` 
  and ``print``, which in Python 2.x were statements, whereas they are functions in Python 3.x. This means 
  that in Python 3.x, a method can be named ``exec()`` or ``print()``, whereas this would lead to a syntax
  error in Python 2.7. Some libraries that do not support 2.x take advantage of this (like PyQt5). Any 
  occurrence of these two keywords as methods in your test code will cause the script to fail converting 
  anything. 
  
  The work around is, luckily, simple: do a global search-replace of ``\.exec\(`` for ``.exec__(`` in your 
  test folder, run nose2pytest, then reverse the search-replace (do a global search-replace of ``\.exec__\(`` 
  for ``.exec(``).
  
- ``@raises``: this decorator can be replaced via the regular expression ``@raises\((.*)\)`` to 
  ``@pytest.mark.xfail(raises=$1)``,
  but I prefer instead to convert such decorated test functions to use ``pytest.raises`` in the test function body.
  Indeed, it is easy to forget the decorator, and add code after the line that raises, but this code will never 
  be run and you won't know. Using the ``pytest.raises(...)`` is better than ``xfail(raise=...)``. 

- Nose2pytest does not have a means of determining if an assertion function is inside a lambda expression, so
  the valid ``lambda: assert_func(a, b)`` gets converted to the invalid ``lambda: assert a operator b``. 
  These should be rare, are easy to spot (your IDE will flag the syntax error, or you will get an exception 
  on import), and are easy to fix by changing from a lambda expression to a local function.
  
I have no doubt that more limitations will arise as nose2pytest gets used on more code bases. Contributions to 
address these and existing limitations are most welcome.
 
 
Other tools
------------

If your test suite is unittest- or unittest2-based, or your Nose tests also use some unittest/2 functionatlity
(such as ``setUp(self)`` method in test classes), then you might find the following useful: 

- https://github.com/pytest-dev/unittest2pytest
- https://github.com/dropbox/unittest2pytest

I have used neither, so I can't make recommendations. However, if your Nose-based test suite uses both Nose/2 and 
unittest/2 functionality (such as ``unittest.case.TestCase`` and/or ``setUp(self)/tearDown(self)`` methods), you 
should be able to run both a unittest2pytest converter, then the nose2pytest converter. 


Solution Notes
---------------

I don't think this script would have been possible without lib2to3, certainly not with the same functionality since 
lib2to3, due to its purpose, preserves newlines, spaces and comments. The documentation for lib2to3 is very 
minimal, so I was lucky to find http://python3porting.com/fixers.html.

Other than figuring out lib2to3 package so I could harness its 
capabilities, some aspects of code transformations still turned out to be tricky, as warned by Regobro in the 
last paragraph of his  `Extending 2to3 <http://python3porting.com/fixers.html>`_ page. 

- Multi-line arguments: Python accepts multi-line expressions when they are surrounded by parentheses, brackets 
  or braces, but not otherwise. For example converting:
  
  .. code-block:: python

    assert_func(long_a +
                 long_b, msg)

  to:
  
  .. code-block:: python

    assert long_a +
               long_b, msg
    
  yields invalid Python code. However, converting to the following yields valid Python code:
  
  .. code-block:: python

    assert (long_a +
               long_b), msg

  So nose2pytest checks each argument expression (such as ``long_a +\n long_b``) to see if it has 
  newlines that would cause an invalid syntax, and if so, wraps them in parentheses. However, it is also important
  for readability of raw assertions that parentheses only be present if necessary. In other words:

  .. code-block:: python

    assert_func((long_a +
                 long_b), msg)
    assert_func(z + (long_a +
                     long_b), msg)

  should convert to:
  
  .. code-block:: python

    assert (long_a +
               long_b), msg
    assert z + (long_a +
                     long_b), msg)
    
  rather than:
  
  .. code-block:: python

    assert ((long_a +
               long_b)), msg
    assert (z + (long_a +
                     long_b)), msg)

  So nose2pytest only tries to limit the addition of external parentheses to code that really needs it. 
   
- Operator precedence: Python assigns a precedence to each operator; operators that are on the same level
  of precedence (like the comparison operators ==, >=, !=, etc) are executed in sequence. This poses a problem 
  for two-argument assertion functions. Example: translating ``assert_equal(a != b, a <= c)`` to 
  ``assert a != b == a <= c`` is incorrect, it must be converted to ``assert (a != b) == (a <= c)``. However
  wrapping every argument in parentheses all the time does not produce easy-to-read assertions:
  ``assert_equal(a, b < c)`` should convert to ``assert a == (b < c)``, not ``assert (a) == (b < c)``. 

  So nose2pytest adds parentheses around its arguments if the operator used between the args has lower precedence 
  than any operator found in the arg.  So ``assert_equal(a, b + c)`` converts to assert ``a == b + c`` whereas
  ``assert_equal(a, b in c)`` converts to ``assert a == (b in c)`` but ``assert_in(a == b, c)`` converts to
  ``assert a == b in c)``.
  

Acknowledgements
----------------

Thanks to (AFAICT) Lennart Regebro for having written http://python3porting.com/fixers.html#find-pattern, and 
to those who answered 
`my question on SO <http://stackoverflow.com/questions/35169154/pattern-to-match-1-or-2-arg-function-call-for-lib2to3>`_
and `my question on pytest-dev <https://mail.python.org/pipermail/pytest-dev/2016-March/003497.html>`_.
