
.. contents::


Overview
------------

This package provides a Python script to convert Nose-based tests into py.test-based tests. Specifically, 
it transforms ``nose.tools.assert_*`` function calls into raw assert statements, while preserving format
of original arguments as much as possible. For example, 

- ``assert_true(a, msg)`` gets converted to ``assert a, msg``  
- ``assert_greater(a, b, msg)`` gets converted to ``assert a > b, msg``  

The script adds parentheses around ``a`` and/or ``b`` if operator precedence would change the interpretation of the 
expression or involves newline. For example, ::

  assert_true(some-long-expression-a in 
              some-long-expression-b, msg)
  assert_equal(a == b, b == c), msg
    
gets converted to ::

  assert (some-long-expression-a in 
              some-long-expression-b), msg
  assert (a == b) == (b == c), msg

A small subset of ``nose.tools.assert_*`` function calls are not 
transformed because there is no raw assert statement equivalent, or the equivalent would be hard to 
maintain. 


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
py.test, is really nice. This is a main reason for using py.test for me. Another reason is the design of fixtures
in py.test.

Switching an existing test suite from Nose to py.test is feasible even without nose2pytest, as it requires 
relatively little work: *relatively* as in, you will probably only need a few modifications, all achievable 
manually, to get the same test coverage and results. A few gotchas: 
  
- test classes that have ``__init__`` will be ignored, those will have to be moved (usually, into class's 
  ``setup_class()``)
- the ``setup.cfg`` may have to be edited since test discovery rules are slightly more strict with py.test
- the order of tests may be different, but in general that should not matter
- all test modules are imported up-front, so some test modules may need adjustment such as moving some 
  code from the top of the test module into its ``setup_module()`` 
    
Once the above has been done to an existing code base, you don't really have to do anything else. However, your test 
suite now has an additional third-party test dependency (Nose), just because of those ``assert_*`` functions used all 
over the place. Moreover, there is no longer one obvious way to do things in your test suite: existing test code 
uses ``nose.tools.assert_*`` functions, yet with py.test you can use raw assertions. If you add tests, which of 
these two approaches should a developer use? If you modify existing tests, should new assertions use raw assert? 
Should the remaining test method, test class, or test module be updated? A test module can contain hundreds of 
calls to ``nose.tools.assert_*`` functions, is a developer to manually go through each one to convert it? Painful and 
error prone, in general not feasible to do manually. 

This is why I developed nose2pytest: I wanted to migrate my pypubsub project's test suite from Nose to py.test,
but also have only py.test as a dependency, and have one obvious way to write assertions in the test suite. 
  

Requirements
-------------

I expect nose2pytest script to run with Python >= 3.4, to correctly convert Python test suite >= 2.7, on any 
OS supported by a version of python that has lib2to3 compatible with Python 3.4's lib2to3. I expect it to 
succeed even with quite old versions of Nose (even prior to 1.0 which came out ca. 2010), and with the new 
Nose2 test driver. 

Note however that I have run the script only with Python 3.4, to convert Python 3.4 test suites based on 
Nose 1.3.7 on Windows 7 Pro 64. If you have successfully used nose2pytest with other combinations, please 
kindly let me know (via github). 


Current Limitations
---------------------

Not every ``nose.tools.assert_*`` function is converted by nose2pytest: 

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
   and change your test code's ``from nose.tools import ...`` statements accordingly. Py.test introspection will 
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

There are other limitations: 

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
  
I have no doubt that more limitations will arise as nose2pytest gets used on code bases. Contributions to 
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
  or braces, but not otherwise. For example converting ::

    assert_func(long_a +
                 long_b, msg)

  to ::

    assert long_a +
               long_b, msg
    
  yields invalid Python code. However, converting to the following yields valid Python code::

    assert (long_a +
               long_b), msg

  So nose2pytest checks each argument expression (such as ``long_a +\n long_b``) to see if it has 
  newlines that would cause an invalid syntax, and if so, wraps them in parentheses. However, it is also important
  for readability of raw assertions that parentheses only be present if necessary. In other words, ::

    assert_func((long_a +
                 long_b), msg)
    assert_func(z + (long_a +
                     long_b), msg)

  should convert to ::

    assert (long_a +
               long_b), msg
    assert z + (long_a +
                     long_b), msg)
    
  rather than ::

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
  
