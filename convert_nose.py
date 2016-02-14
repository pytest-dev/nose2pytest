"""
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

This script uses lib2to3 utility classes that make transforming specific patterns of Python code to
other code.
"""
from lib2to3 import refactor, fixer_base, pygram, pytree, pgen2
from lib2to3.pytree import Node as PyNode, Leaf as PyLeaf
from lib2to3.pgen2 import token

import argparse
import logging
from logging import StreamHandler
import sys
from textwrap import dedent


log = logging.getLogger('nose2pytest')
grammar = pygram.python_grammar
driver = pgen2.driver.Driver(grammar, convert=pytree.convert, logger=log)


PATTERN_ONE_ARG_OR_KWARG = """power< 'func' trailer< '(' not(arglist) obj1=any                         ')' > >"""
PATTERN_ONE_ARG = """power< 'func' trailer< '(' not(arglist | argument<any '=' any>) obj1=any ')' > >"""
PATTERN_ONE_KWARG = """power< 'func' trailer< '(' obj1=argument< any '=' any >                  ')' > >"""
PATTERN_TWO_ARGS_OR_KWARGS = """power< 'func' trailer< '(' arglist< obj1=any ',' obj2=any >              ')' > >"""

PATTERN_1_OR_2_ARGS = """
    power< '{}' trailer< '('
        ( not(arglist | argument<any '=' any>) test=any
        | arglist< test=any ',' msg=any > )
    ')' > >
    """

PATTERN_2_OR_3_ARGS = """
    power< '{}' trailer< '('
        ( arglist< lhs=any ',' rhs=any >
        | arglist< lhs=any ',' rhs=any ',' msg=any > )
    ')' > >
    """


def override_required(func):
    """Decorator used to document that decorated function must be overridden in derived class."""
    return func


def override_optional(func):
    """Decorator used to document that decorated function can be overridden in derived class, but need not be."""
    return func


def override(BaseClass):
    """Decorator used to document that decorated function overrides the function of same name in BaseClass."""
    def decorator(func):
        return func
    return decorator


# FIXERS:

class FixAssertBase(fixer_base.BaseFix):
    # BM_compatible = True

    def __init__(self, nose_func_name: str, pytest_func: str, *args, **kwargs):
        self.PATTERN = self.PATTERN.format(nose_func_name)
        log.info('%s will convert %s as "assert %s"', self.__class__.__name__, nose_func_name, pytest_func)
        super().__init__(*args, **kwargs)

        self.dest_tree = driver.parse_string('assert ' + pytest_func + '\n')
        # remove the \n we added
        del self.dest_tree.children[0].children[1]

    def transform(self, node: PyNode, results: {str: PyNode}) -> PyNode:
        assert results
        dest_tree = self.dest_tree.clone()
        self._transform_dest(dest_tree, results)
        dest_tree.prefix = node.prefix
        return dest_tree

    @override_required
    def _transform_dest(self, node: PyNode, results: {str: PyNode}):
        pass

    def _handle_opt_msg(self, siblings, results):
        if 'msg' in results:
            msg = results["msg"]
            msg = msg.clone()
            siblings.append(PyLeaf(token.STRING, ','))
            siblings.append(msg)


class FixAssert1Arg(FixAssertBase):

    PATTERN = PATTERN_1_OR_2_ARGS

    conversions = dict(
        # assert_true='assert a',
        # assert_false='assert not a',
        assert_is_none='a is None',
        assert_is_not_none='a is not None',
    )

    @override(FixAssertBase)
    def _transform_dest(self, dest_tree, results):
        test = results["test"]
        test = test.clone()
        test.prefix = " "

        node = dest_tree.children[0].children[0].children[1]
        node.children[0] = test
        self._handle_opt_msg(node.children, results)


class FixAssertTrue(FixAssertBase):
    PATTERN = PATTERN_1_OR_2_ARGS

    def __init__(self, *args, **kwargs):
        super().__init__('assert_true', 'a', *args, **kwargs)

    def _transform_dest(self, dest_tree, results):
        test = results["test"]
        test = test.clone()
        test.prefix = " "

        node = dest_tree.children[0].children[0]
        node.children[1] = test
        self._handle_opt_msg(node.children, results)


class FixAssertFalse(FixAssertBase):
    PATTERN = PATTERN_1_OR_2_ARGS

    def __init__(self, *args, **kwargs):
        super().__init__('assert_false', 'not a', *args, **kwargs)

    def _transform_dest(self, dest_tree, results):
        test = results["test"]
        test = test.clone()
        test.prefix = " "

        node = dest_tree.children[0].children[0].children[1]
        node.children[1] = test
        self._handle_opt_msg(node.children, results)


class FixAssert2Args(FixAssertBase):

    PATTERN = PATTERN_2_OR_3_ARGS

    conversions = dict(
        assert_equal='a == b',
        assert_equals='a == b',
        assert_not_equal='a != b',
        assert_not_equals='a != b',

        assert_list_equal='a == b',
        assert_dict_equal='a == b',
        assert_set_equal='a == b',
        assert_sequence_equal='a == b',
        assert_tuple_equal='a == b',
        assert_multi_line_equal='a == b',

        assert_greater='a > b',
        assert_greater_equal='a >= b',
        assert_less='a < b',
        assert_less_equal='a <= b',

        assert_in='a in b',
        assert_not_in='a not in b',

        assert_is='a is b',
        assert_is_not='a is not b',
    )

    @override(FixAssertBase)
    def _transform_dest(self, dest_tree, results):
        lhs = results["lhs"]
        lhs = lhs.clone()
        lhs.prefix = " "

        rhs = results["rhs"]
        rhs = rhs.clone()

        node = dest_tree.children[0].children[0].children[1]
        node.children[0] = lhs
        node.children[2] = rhs
        self._handle_opt_msg(node.children, results)


class NoseConversionRefactoringTool(refactor.MultiprocessRefactoringTool):
    def __init__(self):
        flags = dict(print_function=True)
        super().__init__([], flags)

    def get_fixers(self):
        pre_fixers = []

        for nose_func, pytest_func in FixAssert1Arg.conversions.items():
            pre_fixers.append(FixAssert1Arg(nose_func, pytest_func, self.options, self.fixer_log))
        for nose_func, pytest_func in FixAssert2Args.conversions.items():
            pre_fixers.append(FixAssert2Args(nose_func, pytest_func, self.options, self.fixer_log))

        pre_fixers.append(FixAssertTrue(self.options, self.fixer_log))
        pre_fixers.append(FixAssertFalse(self.options, self.fixer_log))

        return pre_fixers, []


def test():
    test_script = dedent("""
        log.print("hi")

        assert_true(a)
        assert_true(a, msg)
        assert_false(a)
        assert_false(a, msg='text')

        assert_is_none(a)
        assert_is_none(a, text)
        assert_is_none(a, msg=text)

        assert_in(a, b)
        assert_in(a, b, text)
        assert_in(a, b, msg='text')

        """)

    for key in FixAssert1Arg.conversions:
        test_script += '{}(123)\n'.format(key)
    for key in FixAssert2Args.conversions:
        test_script += '{}(123, 456)\n'.format(key)
    log.info(test_script)

    result = refac.refactor_string(test_script, 'script')
    log.info(result)


def setup():
    # from nose import tools as nosetools
    # import inspect
    # for key in dir(nosetools):
    #     if key.startswith('assert_'):
    #         argspec = inspect.getargspec(getattr(nosetools, key))
    #         print(key, argspec)

    redirect = StreamHandler(stream=sys.stdout)
    redirect.setLevel(logging.DEBUG)
    log.addHandler(redirect)
    log.setLevel(logging.DEBUG)

    parser = argparse.ArgumentParser(description='Convert nose assertions to regular assertions for use by pytest')
    parser.add_argument('dir_name', type=str,
                        help='folder name from which to start; all .py files under it will be converted')
    parser.add_argument('-w', dest='write', action='store_false',
                        help='disable overwriting of original files')

    return parser.parse_args()


args = setup()
refac = NoseConversionRefactoringTool()
# test()
refac.refactor_dir(args.dir_name, write=args.write)

