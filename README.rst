# nose2pytest

Overview
------------

This package provides a Python script to convert Nose-based tests into py.test-based tests. Specifically, 
it transforms ``nose.tools.assert_*`` function calls into raw assert statements, while preserving format
of original arguments as much as possible. For example, 

- ``assert_true(a[, msg])`` gets converted to ``assert a[, msg]``  
- ``assert_greater(a, b[, msg])`` gets converted to ``assert a > b[, msg]``  

The script adds parentheses around ``a`` and/or ``b`` if operator precedence would change the interpretation of the 
expression or involves newline::

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


Running
------------

Run this script, giving it a folder to convert: it will find all .py files in the folder tree and 
overwrite the original. Type ``nose2pytest -h`` for other options, such as -v. 


Motivation
------------

- This script makes it feasible to decrease the number of test dependencies of a code base. This is always a good thing.
- Once a test suite is migrated from Nose to py.test, old test code remains that uses ``nose.tools.assert_*``
  functions. Although new test code can be written in terms of raw assertions that py.test will introspect,  
  it is better to have one obvious way to do things, and to be consistent; hence once the migration done, 
  all assertions that have a readable, maintainable representation as raw assertions should be transformed so 
  developers have one rule to follow in test code: use assert statements whenever possible. 
- Developers tend to copy code so if test code uses ``assert_*`` functions then new test code is likely going to 
  use it too, and one of the benefits of using py.test is diminished.
- I often have to write the assertion expression first before I can decide which Nose assertion function to use:
  do I want assert_equal, assert_is, assert_is_none, etc. With raw assert, I just write. 
  

Requirements
-------------

The script has so far only been tested with Python 3.4. The test platform has been so far only Windows 7 Pro 64, 
but I don't expect any platform incompatibilities. 


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
    
    Nose2pytest distribution contains a module, ``assert_tools.py`` which defines these utility functions to simply 
    contain the equivalent raw assert statement. Copy the module into your test folder or into the pytest package 
    and change your test code's ``from nose.tools import ...`` statements accordingly. You will still get the 
    py.test introspection
    
3. Some Nose functions don't have a one-line assert statement equivalent, they have to remain utility functions:

    - ``assert_logs``
    - ``assert_raises_regex``
    - ``assert_raises_regexp``  # deprecated by Nose
    - ``assert_regexp_matches`` # deprecated by Nose
    - ``assert_warns_regex``
    
4. Some Nose functions simply weren't on my radar; for example I just noticed there is a ``nose.tools.ok_()`` 
   function which is the same as ``assert_equal``, I had never noticed it before. Feel free to contribute via email
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
  

