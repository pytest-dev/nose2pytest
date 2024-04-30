.. image:: https://badge.fury.io/py/nose2pytest.svg
    :target: https://badge.fury.io/py/nose2pytest
.. image:: https://github.com/pytest-dev/nose2pytest/workflows/Test/badge.svg
    :target: https://github.com/pytest-dev/nose2pytest/actions


.. contents::


Overview
-------------

This package provides a Python script and pytest plugin to help convert Nose-based tests into pytest-based
tests. Specifically, the script transforms ``nose.tools.assert_*`` function calls into raw assert statements, 
while preserving the format of original arguments as much as possible. For example, the script:

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


Running
------------

For a one-time conversion use the shell command ::

  pipx run --python 3.11 nose2pytest path/to/dir/with/python_files
  
This will find all ``.py`` files in the folder tree starting at ``path/to/dir/with/python_files`` and 
overwrite the original (assuming most users will be running this on a version-controlled code base, this is
almost always what would be most convenient). Type ``nose2pytest -h`` for other options, such as ``-v``. 


Installation
-------------

For doing multiple conversions use the shell command ::

  pipx install --python 3.11 nose2pytest

For each conversion use the shell command ::

  nose2pytest path/to/dir/with/python_files


Motivation
------------

I have used Nose for years and it is a great tool. However, to get good test failure diagnostics with Nose you 
ought to use the ``assert_*()`` functions from ``nose.tools``. Although they provide very good diagnostics, they 
are not as convenient to use as raw assertions, since you have to decide beforehand what type of assertion you 
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
- the order of tests may be different, but in general, that should not matter
- all test modules are imported up-front, so some test modules may need adjustment such as moving some 
  code from the top of the test module into its ``setup_module()`` 
    
Once the above has been done to an existing code base, you don't really have to do anything else. However, your test 
suite now has an additional third-party test dependency (Nose), just because of those ``assert_*`` functions used all 
over the place. Moreover, there is no longer one obvious way to do things in your test suite: existing test code 
uses ``nose.tools.assert_*`` functions, yet with pytest you can use raw assertions. If you add tests, which of
these two approaches should a developer use? If you modify existing tests, should new assertions use raw assert? 
Should the remaining test method, test class, or test module be updated? A test module can contain hundreds of 
calls to ``nose.tools.assert_*`` functions, is a developer to manually go through each one to convert it? Painful and 
error-prone, in general not feasible to do manually. 

This is why I developed nose2pytest: I wanted to migrate my pypubsub project's test suite from Nose to pytest,
but also have only pytest as a dependency, and have one obvious way to write assertions in the test suite.
  

Requirements
-------------

I expect nose2pytest script to run with supported versions of CPython <= v3.11, on any OS supported by a version of
Python that has lib2to3 compatible with fissix. I expect it to succeed even with quite old versions of Nose (even
prior to 1.0 which came out ca. 2010) and with the new Nose2 test driver. 

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
assert_not_equal(a,b[, msg])                 assert a != b[, msg]
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
assert_almost_equal(a,b[, msg])              assert a == pytest.approx(b, abs=1e-7)[, msg]
assert_almost_equal(a,b, delta[, msg])       assert a == pytest.approx(b, abs=delta)[, msg]
assert_almost_equal(a, b, places[, msg])     assert a == pytest.approx(b, abs=1e-places)[, msg]
assert_not_almost_equal(a,b[, msg])          assert a != pytest.approx(b, abs=1e-7)[, msg]
assert_not_almost_equal(a,b, delta[, msg])   assert a != pytest.approx(b, abs=delta)[, msg]
assert_not_almost_equal(a,b, places[, msg])  assert a != pytest.approx(b, abs=1e-places)[, msg]
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
  conversions be removed? Should an ``import pytest`` statement be added, and if so, where? If it is added after
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
  
  The possibilities are endless so supporting this would require such a large amount of time that I 
  do not have. As with other limitations in this section

- Nose functions that can be used as context managers can obviously not be converted to raw assertions. 
  However, there is currently no way of preventing nose2pytest from converting Nose functions used this way. 
  You will have to manually fix.
    
- ``@raises``: this decorator can be replaced via the regular expression ``@raises\((.*)\)`` to 
  ``@pytest.mark.xfail(raises=$1)``,
  but I prefer instead to convert such decorated test functions to use ``pytest.raises`` in the test function body.
  Indeed, it is easy to forget the decorator and add code after the line that raises, but this code will never 
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

I don't think this script would have been possible without lib2to3/fissix, certainly not with the same
functionality since lib2to3/fissix, due to their purpose, preserves newlines, spaces and comments. The
documentation for lib2to3/fissix is very minimal, so I was lucky to
find http://python3porting.com/fixers.html.

Other than figuring out lib2to3/fissix package so I could harness its capabilities, some aspects of code
transformations still turned out to be tricky, as warned by Regobro in the last paragraph of his
`Extending 2to3 <http://python3porting.com/fixers.html>`_ page. 

- Multi-line arguments: Python accepts multi-line expressions when they are surrounded by parentheses, brackets 
  or braces, but not otherwise. For example, converting:
  
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
  for the readability of raw assertions that parentheses only be present if necessary. In other words:

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
   
- Operator precedence: Python assigns precedence to each operator; operators that are on the same level
  of precedence (like the comparison operators ==, >=, !=, etc) are executed in sequence. This poses a problem 
  for two-argument assertion functions. Example: translating ``assert_equal(a != b, a <= c)`` to 
  ``assert a != b == a <= c`` is incorrect, it must be converted to ``assert (a != b) == (a <= c)``. However,
  wrapping every argument in parentheses all the time does not produce easy-to-read assertions:
  ``assert_equal(a, b < c)`` should convert to ``assert a == (b < c)``, not ``assert (a) == (b < c)``. 

  So nose2pytest adds parentheses around its arguments if the operator used between the args has lower precedence 
  than any operator found in the arg.  So ``assert_equal(a, b + c)`` converts to assert ``a == b + c`` whereas
  ``assert_equal(a, b in c)`` converts to ``assert a == (b in c)`` but ``assert_in(a == b, c)`` converts to
  ``assert a == b in c)``.
  

Contributing
------------

Patches and extensions are welcome. Please fork, branch, and then submit PR. Nose2pytest uses `lib2to3.pytree`,
in particular the Leaf and Node classes. There are a few particularly challenging aspects to transforming
nose test expressions to equivalent pytest expressions:

#. Finding expressions that match a pattern: If the code you want to transform does not already match one
   of the uses cases in script.py, you will have to determine the lib2to3/fissix pattern expression
   that describes it (this is similar to regular expressions, but for AST representation of code,
   instead of text strings). Various expression patterns already exist near the top of
   nose2pytest/script.py. This is largely trial and error as there is (as of this writing) no good
   documentation.
#. Inserting the sub-expressions extracted by lib2to3/fissix in step 1 into the target "expression template".
   For example to convert `assert_none(a)` to `assert a is None`, the `a` sub-expression extracted via the
   lib2to3/fissix pattern must be inserted into the correct "placeholder" node of the target expression. If
   step 1 was necessary, then step 2 like involves creating a new class that derives from `FixAssertBase`.
#. Parentheses and priority of operators: sometimes, it is necessary to add parentheses around an extracted
   subexpression to protect it against higher-priority operators. For example, in `assert_none(a)` the `a`
   could be an arbitrary Python expression, such as `var1 and var2`. The meaning of `assert_none(var1 and var2)`
   is not the same as `assert var1 and var2 is None`; parentheses must be added i.e. the target expression
   must be `assert (var1 and var2) is None`. Whether this is necessary depends on the transformation. The
   `wrap_parens_*` functions provide examples of how and when to do this.
#. Spacing: white space and newlines in code must be preserved as much as possible, and removed
   when unnecessary. For example, `assert_equal(a, b)` convers to `assert a == b`; the latter already has a
   a space before the b, but so does the original; the `lib2to3.pytree` captures such 'non-code' information
   so that generating Python code from a Node yields the same as the input if no transformations were applied.
   This is done via the `Node.prefix` property.

When the pattern is correctly defined in step 1, adding a test in tests/test_script.py for a string that
contains Python code that matches it will cause the `FixAssertBase.transform(node, results)` to be called,
with `node` being the Node for which the children match the defined pattern. The `results` is map of object
names defined in the pattern, to the Node subtree representing the sub-expression matched. For example,
a pattern for `assert_none(a)` (where `a` could be any sub-expression such as `1+2` or `sqrt(5)` or
`var1+var2`) will cause `results` to contain the sub-expression that `a` represents. The objective of
`transform()` is then to put the extracted results at the correct location into a new Node tree that
represents the target (transformed) expression.

Nodes form a tree, each Node has a `children` property, containing 0 or more Node and/or Leaf. For example,
if `node` represents `assert a/2 == b`, then the tree might be something like this::

  node (Node)
      assert (Leaf)
      node (node)
          node (node)
              a (Leaf)
              / (Leaf)
              2 (Leaf)
          ==  (Leaf)
          b (Leaf)

Sometimes you may be able to guess what the tree is for a given expression, however most often it is best to use
a debugger to run a test that attempts to transform your expression of interest (there are several examples of
how to do this in tests/test_script.py), break at the beginning of the `FixAssertBase.transform()` method, and
explore the `node.children` tree to find the subexpressions that you need to extract. In the above example,
the `assert` leaf node is child at index 0 of `node.children`, whereas child 1 is another Node; the `a` leaf
is child 0 of child 0 of child 1 of `node.children`, i.e. it is `node.children[0].children[0].children[1]`.
Therefore the "path" from `node` to reach 'a' is (0, 0, 1).

The main challenge for this step of nose2test extension is then to find the paths to reach the desired
"placeholder" objects in the target expression. For example if `assert_almost_equal(a, b, delta=value)`
must be converted to `assert a == pytest.approx(b, delta=value)`, then the nodes of interest are a, b, and
delta, and their paths are 0, (2, 2, 1, 0) and (2, 2, 1, 2, 2) respectively (when a path contains only
1 item, there is no need to use a tuple).


Releasing
---------

See `RELEASING.rst <RELEASING.rst>`__.

Maintenance
-----------

- Clone or fork the git repo, create a branch
- Install `pytest` and `nose` on your system: `python -m pip install pytest nose`
- In the root folder, run `pytest`
- Once all tests pass, install tox on your system: on Ubuntu, `python -m pip install tox`
- Run tox: `tox`
- Add a python version if the latest Python is not in `tox.ini`

.. note::

    Notes for Ubuntu:

    My experience today installing python 3.5 to 3.11 on Ubuntu 18 was surprisingly not smooth. I had to use these commands:

    * sudo apt install python3.5 (ok)
    * sudo apt install python3.x-distutils for x=9,10,11
    * had to use `python -m pip` intead of just `pip` otherwise wrong version would get found
    * used `sudo update-alternatives --install /usr/bin/python python /usr/bin/python3.x 1` for all x
    * used `sudo update-alternatives --config python` to choose which python active
    * had to install setuptools from git repo otherwise weird pip error (used https://stackoverflow.com/a/69573368/869951)
    * note however that once the correct tox installed,


Acknowledgments
---------------

Thanks to (AFAICT) Lennart Regebro for having written http://python3porting.com/fixers.html#find-pattern, and 
to those who answered 
`my question on SO <http://stackoverflow.com/questions/35169154/pattern-to-match-1-or-2-arg-function-call-for-lib2to3>`_
and `my question on pytest-dev <https://mail.python.org/pipermail/pytest-dev/2016-March/003497.html>`_.
