# Copyright 2016 Oliver Schoenborn. BSD 3-Clause license (see LICENSE file for details).
"""
This script defines lib2to3 fixers and uses lib2to3 utility classes to transform specific patterns of
Python AST code for the nose.tools.assert_* functions into raw assert functions that can be executed by
pytest without all the error-trapping code used by nose.

The following article was very useful: http://python3porting.com/fixers.html#find-pattern.
"""

import argparse
import logging

from lib2to3 import refactor, fixer_base, pygram, pytree, pgen2
from lib2to3.pytree import Node as PyNode, Leaf as PyLeaf
from lib2to3.pgen2 import token
from lib2to3.fixer_util import parenthesize


log = logging.getLogger('nose2pytest')


def override_required(func):
    """Decorator used to document that the decorated function must be overridden in derived class."""
    return func


def override_optional(func):
    """Decorator used to document that the decorated function can be overridden in derived class, but need not be."""
    return func


def override(BaseClass):
    """Decorator used to document that the decorated function overrides the function of same name in BaseClass."""

    def decorator(func):
        return func

    return decorator


# FIXERS:

grammar = pygram.python_grammar
driver = pgen2.driver.Driver(grammar, convert=pytree.convert, logger=log)


PATTERN_ONE_ARG_OR_KWARG =   """power< 'func' trailer< '(' not(arglist) obj1=any                         ')' > >"""
PATTERN_ONE_ARG =            """power< 'func' trailer< '(' not(arglist | argument<any '=' any>) obj1=any ')' > >"""
PATTERN_ONE_KWARG =          """power< 'func' trailer< '(' obj1=argument< any '=' any >                  ')' > >"""
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


# for the following node types, contains_newline() will return False even if newlines are between ()[]{}
NEWLINE_OK_TOKENS = (token.LPAR, token.LSQB, token.LBRACE)


def contains_newline(node: PyNode) -> bool:
    """
    Returns True if any of the children of node have a prefix containing \n, or any of their children recursively.
    Returns False if no non-bracketed children are found that have such prefix. Example: node of 'a\n  in b' would
    return True, whereas '(a\n   b)' would return False.
    """
    for child in node.children:
        if child.type in NEWLINE_OK_TOKENS:
            return False
        if '\n' in child.prefix:
            return True
        if isinstance(child, PyNode) and contains_newline(child):
            return True

    return False


class FixAssertBase(fixer_base.BaseFix):
    # BM_compatible = True

    # Each derived class should define a dictionary where the key is the name of the nose function to convert,
    # and the value is a pair where the first item is the assertion statement expression, and the second item
    # is data that will be available in _transform_dest() override as self._conv_data.
    conversions = None

    @classmethod
    def create_all(cls, *args, **kwargs) -> [fixer_base.BaseFix]:
        """
        Create an instance for each key in cls.conversions, assumed to be defined by derived class.
        The *args and **kwargs are those of BaseFix.
        :return: list of instances created
        """
        fixers = []
        for nose_func in cls.conversions:
            fixers.append(cls(nose_func, *args, **kwargs))
        return fixers

    def __init__(self, nose_func_name: str, *args, **kwargs):
        test_expr, conv_data = self.conversions[nose_func_name]
        self.nose_func_name = nose_func_name
        self._conv_data = conv_data

        self.PATTERN = self.PATTERN.format(nose_func_name)
        log.info('%s will convert %s as "assert %s"', self.__class__.__name__, nose_func_name, test_expr)
        super().__init__(*args, **kwargs)

        self.dest_tree = driver.parse_string('assert ' + test_expr + '\n')
        # remove the \n we added
        del self.dest_tree.children[0].children[1]

    @override(fixer_base.BaseFix)
    def transform(self, node: PyNode, results: {str: PyNode}) -> PyNode:
        assert results
        dest_tree = self.dest_tree.clone()
        assert_arg_test_node = self._get_node(dest_tree, (0, 0, 1))
        assert_args = assert_arg_test_node.parent
        self._transform_dest(assert_arg_test_node, results)

        assert_arg_test_node = self._get_node(dest_tree, (0, 0, 1))
        if contains_newline(assert_arg_test_node):
            prefixes = assert_arg_test_node.prefix.split('\n', 1)
            assert_arg_test_node.prefix = '\n'+prefixes[1] if len(prefixes) > 1 else ''
            new_node = parenthesize(assert_arg_test_node.clone())
            new_node.prefix = prefixes[0] or ' '
            assert_arg_test_node.replace(new_node)

        self.__handle_opt_msg(assert_args, results)

        dest_tree.prefix = node.prefix
        return dest_tree

    @override_required
    def _transform_dest(self, assert_arg_test_node: PyNode, results: {str: PyNode}):
        """
        Transform the given node to use the results.
        :param assert_arg_test_node: the destination node representing the assertion test argument
        :param results: the results of pattern matching
        """
        pass

    def _get_node(self, from_node, indices_path: None or int or [int]) -> PyLeaf or PyNode:
        """
        Get a node relative to another node.
        :param from_node: the node from which to start
        :param indices_path: the path through children
        :return: node found (could be leaf); if indices_path is None, this is from_node itself; if it is a
            number, return from_node[indices_path]; else returns according to sequence of children indices

        Example: if indices_path is (1, 2, 3), will return from_node.children[1].children[2].children[3].
        """
        if indices_path is None:
            return from_node

        try:
            node = from_node
            for index in indices_path:
                node = node.children[index]
            return node

        except TypeError:
            return from_node.children[indices_path]

    def __handle_opt_msg(self, assertion_args_node: PyNode, results: {str: PyNode}):
        """
        Append a message argument to assertion args node, if one appears in results.
        :param assertion_args_node: the node representing all the arguments of assertion function
        :param results: results from pattern matching
        """
        if 'msg' in results:
            msg = results["msg"]
            msg = msg.clone()
            siblings = assertion_args_node.children
            siblings.append(PyLeaf(token.COMMA, ','))
            siblings.append(msg)


class FixAssert1ArgAopB(FixAssertBase):
    """
    Fixer class for any 1-argument assertion function (assert_func(a)). It supports optional 2nd arg for the
    assertion message, ie assert_func(a, msg) -> assert a binop something, msg.
    """

    PATTERN = PATTERN_1_OR_2_ARGS

    # the conv data is a node children indices path from the PyNode that represents the assertion expression.
    # Example: assert_false(a) becomes "assert not a", so the PyNode for assertion expression is 'not a', and
    # the 'a' is its children[1] so self._conv_data needs to be 1.
    conversions = dict(
        assert_true=('a', None),
        assert_false=('not a', 1),
        assert_is_none=('a is None', 0),
        assert_is_not_none=('a is not None', 0),
    )

    @override(FixAssertBase)
    def _transform_dest(self, assert_arg_test_node: PyNode, results: {str: PyNode}):
        test = results["test"]
        test = test.clone()
        test.prefix = " "

        # the destination node for 'a' is in conv_data:
        dest_node = self._get_node(assert_arg_test_node, self._conv_data)
        dest_node.replace(test)


class FixAssert2ArgsAopB(FixAssertBase):
    """
    Fixer class for any 2-argument assertion function (assert_func(a, b)). It supports optional third arg
    as the assertion message, ie assert_func(a, b, msg) -> assert a binop b, msg.

    The class defines a conversions dict
    """

    PATTERN = PATTERN_2_OR_3_ARGS

    # The conversion data (2nd item of the value; see base class docs) is a pair of "node paths": the first
    # node path is to "a", the second one is to "b", relative to the assertion expression.
    #
    # Example 1: assert_equal(a, b) will convert to "assert a == b" so the PyNode for assertion expression
    # is 'a == b' and a is that node's children[0], whereas b is that node's children[2], so the self._conv_data
    # is simply (0, 2).
    #
    # Example 2: assert_is_instance(a, b) converts to "assert isinstance(a, b)" so the conversion data is
    # the pair of node paths (1, 1, 0) and (1, 1, 1) since from the PyNode for the assertion expression
    # "isinstance(a, b)", 'a' is that node's children[1].children[1].children[0], whereas 'b' is
    # that node's children[1].children[1].children[1].
    conversions = dict(
        assert_equal=('a == b', (0, 2)),
        assert_equals=('a == b', (0, 2)),
        assert_not_equal=('a != b', (0, 2)),
        assert_not_equals=('a != b', (0, 2)),

        assert_list_equal=('a == b', (0, 2)),
        assert_dict_equal=('a == b', (0, 2)),
        assert_set_equal=('a == b', (0, 2)),
        assert_sequence_equal=('a == b', (0, 2)),
        assert_tuple_equal=('a == b', (0, 2)),
        assert_multi_line_equal=('a == b', (0, 2)),

        assert_greater=('a > b', (0, 2)),
        assert_greater_equal=('a >= b', (0, 2)),
        assert_less=('a < b', (0, 2)),
        assert_less_equal=('a <= b', (0, 2)),

        assert_in=('a in b', (0, 2)),
        assert_not_in=('a not in b', (0, 2)),

        assert_is=('a is b', (0, 2)),
        assert_is_not=('a is not b', (0, 2)),

        assert_is_instance=('isinstance(a, b)', ((1, 1, 0), (1, 1, 1), False)),
        assert_count_equal=('collections.Counter(a) == collections.Counter(b)', ((0, 2, 1), (2, 2, 1), False)),
        assert_not_regex=('not re.search(b, a)', ((1, 2, 1, 2), (1, 2, 1, 0), False)),
        assert_regex=('re.search(b, a)', ((2, 1, 2), (2, 1, 0), False)),
        assert_almost_equals=('abs(a - b) <= delta', ((0, 1, 1, 0), (0, 1, 1, 2))),
        assert_not_almost_equal=('abs(a - b) > delta', ((0, 1, 1, 0), (0, 1, 1, 2))),
    )

    @override(FixAssertBase)
    def _transform_dest(self, assert_arg_test_node: PyNode, results: {str: PyNode}):
        lhs = results["lhs"]
        lhs_prefix = lhs.prefix
        lhs = lhs.clone()
        lhs.prefix = lhs_prefix + " "

        rhs = results["rhs"]
        rhs = rhs.clone()

        dest1 = self._get_node(assert_arg_test_node, self._conv_data[0])
        dest2 = self._get_node(assert_arg_test_node, self._conv_data[1])

        dest1.replace(self.__group_if_non_leaf(lhs))
        dest2.replace(self.__group_if_non_leaf(rhs))

    def __group_if_non_leaf(self, node: PyNode or PyLeaf) -> PyNode or PyLeaf:
        """
        If the conversion data indicates that a, b should be grouped (wrapped by parentheses), then
        return node if node is a leaf, and return parenthesized node otherwise.
        :param node: the node to parenthesize
        :return: the node for the parenthesized expression, or the node itself
        """
        maybe_needed = len(self._conv_data) <= 2 or self._conv_data[2]
        if maybe_needed and isinstance(node, PyNode):
            new_node = parenthesize(node)
            new_node.prefix = node.prefix
            node.prefix = ''
            return new_node

        return node


# ------------ Main portion of script -------------------------------

class NoseConversionRefactoringTool(refactor.MultiprocessRefactoringTool):
    def __init__(self):
        flags = dict(print_function=True)
        super().__init__([], flags)

    def get_fixers(self):
        pre_fixers = []
        post_fixers = []

        pre_fixers.extend(FixAssert1ArgAopB.create_all(self.options, self.fixer_log))
        pre_fixers.extend(FixAssert2ArgsAopB.create_all(self.options, self.fixer_log))

        return pre_fixers, post_fixers


def setup():
    # from nose import tools as nosetools
    # import inspect
    # for key in dir(nosetools):
    #     if key.startswith('assert_'):
    #         argspec = inspect.getargspec(getattr(nosetools, key))
    #         print(key, argspec)

    parser = argparse.ArgumentParser(description='Convert nose assertions to regular assertions for use by pytest')
    parser.add_argument('dir_name', type=str,
                        help='folder name from which to start; all .py files under it will be converted')
    parser.add_argument('-w', dest='write', action='store_false',
                        help='disable overwriting of original files')

    return parser.parse_args()


if __name__ == '__main__':
    args = setup()
    refac = NoseConversionRefactoringTool()
    refac.refactor_dir(args.dir_name, write=args.write)

