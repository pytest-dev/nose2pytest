#! python
"""
Copyright 2016 Oliver Schoenborn. BSD 3-Clause license (see __license__ at bottom of this file for details).

This script transforms nose.tools.assert_* function calls into raw assert statements, while preserving format
of original arguments as much as possible. A small subset of nose.tools.assert_* function calls is not
transformed because there is no raw assert statement equivalent. However, if you don't use those functions
in your code, you will be able to remove nose as a test dependency of your library/app.

Requires Python 3.4.

This script relies heavily on fissix, using it to find patterns of code to transform and convert transformed
code nodes back into Python source code. The following article was very useful:
http://python3porting.com/fixers.html#find-pattern.
"""

import sys
import argparse
import logging
from pathlib import Path

from fissix import refactor, fixer_base, pygram, pytree, pgen2
from fissix.pytree import Node as PyNode, Leaf as PyLeaf
from fissix.pgen2 import token
from fissix.fixer_util import parenthesize

__version__ = "1.0.12"

log = logging.getLogger('nose2pytest')


def override_required(func: callable):
    """Decorator used to document that the decorated function must be overridden in derived class."""
    return func


def override_optional(func: callable):
    """Decorator used to document that the decorated function can be overridden in derived class, but need not be."""
    return func


def override(BaseClass):
    """Decorator used to document that the decorated function overrides the function of same name in BaseClass."""

    def decorator(func):
        return func

    return decorator


# Transformations:

grammar = pygram.python_grammar
driver = pgen2.driver.Driver(grammar, convert=pytree.convert, logger=log)

PATTERN_ONE_ARG_OR_KWARG = """
    power< 'func' trailer< '(' 
        not(arglist) obj1=any
    ')' > >
    """

PATTERN_ONE_ARG = """
    power< 'func' trailer< '(' 
        not(arglist | argument<any '=' any>) obj1=any 
    ')' > >"""

PATTERN_ONE_KWARG = """
    power< 'func' trailer< '(' 
        obj1=argument< any '=' any >                  
    ')' > >"""

PATTERN_TWO_ARGS_OR_KWARGS = """
    power< 'func' trailer< '(' 
        arglist< obj1=any ',' obj2=any >              
    ')' > >"""

PATTERN_1_OR_2_ARGS = """
    power< '{}' trailer< '('
        ( not(arglist | argument<any '=' any>) test=any
        | arglist< test=any ',' msg=any > )
    ')' > >
    """

PATTERN_2_OR_3_ARGS = """
    power< '{}' trailer< '('
        ( arglist< lhs=any ',' rhs=any [','] >
        | arglist< lhs=any ',' rhs=any ',' msg=any > )
    ')' > >
    """

PATTERN_ALMOST_ARGS = """
    power< '{}' trailer< '('
        ( arglist< aaa=any ',' bbb=any [','] >
        | arglist< aaa=any ',' bbb=any ',' arg3=any [','] >
        | arglist< aaa=any ',' bbb=any ',' arg3=any ',' arg4=any > )
    ')' > >
    """

# for the following node types, contains_newline() will return False even if newlines are between ()[]{}
NEWLINE_OK_TOKENS = (token.LPAR, token.LSQB, token.LBRACE)

# these operators require parens around function arg if binop is ==, !=, ...
COMPARISON_TOKENS = (token.EQEQUAL, token.NOTEQUAL, token.LESS, token.LESSEQUAL, token.GREATER, token.GREATEREQUAL)

if sys.version_info.major < 3:
    raise RuntimeError('nose2pytest must be run using Python 3.x')

py_grammar_symbols = pygram.python_grammar.symbol2number

GRAM_SYM = py_grammar_symbols['comparison']
COMP_OP = py_grammar_symbols['comp_op']
MEMBERSHIP_SYMBOLS = (
    (GRAM_SYM, 1, 'in'),
    (GRAM_SYM, COMP_OP, 'not in')
)
IDENTITY_SYMBOLS = (
    (GRAM_SYM, 1, 'is'),
    (GRAM_SYM, COMP_OP, 'is not')
)
BOOLEAN_OPS = (
    (py_grammar_symbols['not_test'], 1, 'not'),
    (py_grammar_symbols['and_test'], 1, 'and'),
    (py_grammar_symbols['or_test'], 1, 'or')
)
GENERATOR_TYPE = py_grammar_symbols['argument']

# these operators require parens around function arg if binop is + or -
ADD_SUB_GROUP_TOKENS = (
    token.PLUS, token.MINUS,
    token.RIGHTSHIFT, token.LEFTSHIFT,
    token.VBAR, token.AMPER, token.CIRCUMFLEX,
)


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


def wrap_parens(arg_node: PyNode, checker_fn: callable) -> PyNode or PyLeaf:
    """
    If a node that represents an argument to assert_ function should be grouped, return a new node that adds
    parentheses around arg_node. Otherwise, return arg_node.
    :param arg_node: the arg_node to parenthesize
    :return: the arg_node for the parenthesized expression, or the arg_node itself
    """
    if isinstance(arg_node, PyNode) and checker_fn(arg_node):
        # log.info('adding parens: "{}" ({}), "{}" ({})'.format(first_child, first_child.type, sibling, sibling.type))
        # sometimes arg_node has parent, need to remove it before giving to parenthesize() then re-insert:
        parent = arg_node.parent
        if parent is not None:
            pos_parent = arg_node.remove()
            new_node = parenthesize(arg_node)
            parent.insert_child(pos_parent, new_node)
        else:
            new_node = parenthesize(arg_node)

        new_node.prefix = arg_node.prefix
        arg_node.prefix = ''
        return new_node

    return arg_node


def is_if_else_op(node: PyNode) -> bool:
    return (len(node.children) == 5 and
            node.children[1] == PyLeaf(token.NAME, 'if') and
            node.children[3] == PyLeaf(token.NAME, 'else')
            )


def has_weak_op_for_comparison(node: PyNode) -> bool:
    """Test if node contains operators that are weaking than comparison operators"""

    if is_if_else_op(node):
        return True

    for child in node.children:
        if child.type in NEWLINE_OK_TOKENS:
            return False

        # comparisons and boolean combination:
        binop_type = child.type
        if binop_type in COMPARISON_TOKENS:
            return True

        # membership and identity tests:
        binop_name = str(child).strip()
        symbol = (node.type, binop_type, binop_name)
        if symbol in BOOLEAN_OPS or symbol in MEMBERSHIP_SYMBOLS or symbol in IDENTITY_SYMBOLS:
            return True

        # continue into children that are nodes:
        if isinstance(child, PyNode) and has_weak_op_for_comparison(child):
            return True

    return False


def wrap_parens_for_comparison(arg_node: PyNode or PyLeaf) -> PyNode or PyLeaf:
    """
    Assuming arg_node represents an argument to an assert_ function that uses comparison operators, then if
    arg_node has any operators that have equal or weaker precedence than those operators (including
    membership and identity test operators), return a new node that adds parentheses around arg_node.
    Otherwise, return arg_node.

    :param arg_node: the arg_node to parenthesize
    :return: the arg_node for the parenthesized expression, or the arg_node itself
    """
    return wrap_parens(arg_node, has_weak_op_for_comparison)


def has_weak_op_for_addsub(node: PyNode, check_comparison: bool = True) -> bool:
    if check_comparison and has_weak_op_for_comparison(node):
        return True

    for child in node.children:
        if child.type in NEWLINE_OK_TOKENS:
            return False

        if child.type in ADD_SUB_GROUP_TOKENS:
            return True

        # continue into children that are nodes:
        if isinstance(child, PyNode) and has_weak_op_for_addsub(child, check_comparison=False):
            return True

    return False


def wrap_parens_for_addsub(arg_node: PyNode or PyLeaf) -> PyNode or PyLeaf:
    """
    Assuming arg_node represents an argument to an assert_ function that uses + or - operators, then if
    arg_node has any operators that have equal or weaker precedence than those operators, return a new node
    that adds parentheses around arg_node. Otherwise, return arg_node.

    :param arg_node: the arg_node to parenthesize
    :return: the arg_node for the parenthesized expression, or the arg_node itself
    """
    return wrap_parens(arg_node, has_weak_op_for_addsub)


def get_prev_sibling(node: PyNode) -> PyNode:
    if node is None:
        return None  # could not find
    if node.prev_sibling is not None:
        return node.prev_sibling
    return get_prev_sibling(node.parent)


def adjust_prefix_first_arg(node: PyNode or PyLeaf, orig_prefix: str):
    if get_prev_sibling(node).type != token.NAME:
        node.prefix = ''
    else:
        node.prefix = orig_prefix or " "


class FixAssertBase(fixer_base.BaseFix):
    # BM_compatible = True

    # Each derived class should define a dictionary where the key is the name of the nose function to convert,
    # and the value is a pair where the first item is the assertion statement expression, and the second item
    # is data that will be available in _transform_dest() override as self._arg_paths.
    conversions = None

    DEFAULT_ARG_PATHS = None

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
        if self.DEFAULT_ARG_PATHS is None:
            test_expr, conv_data = self.conversions[nose_func_name]
            self._arg_paths = conv_data
        else:
            test_expr = self.conversions[nose_func_name]
            self._arg_paths = self.DEFAULT_ARG_PATHS

        self.nose_func_name = nose_func_name

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

        if self._transform_dest(assert_arg_test_node, results):
            assert_arg_test_node = self._get_node(dest_tree, (0, 0, 1))
            if contains_newline(assert_arg_test_node):
                prefixes = assert_arg_test_node.prefix.split('\n', 1)
                assert_arg_test_node.prefix = '\n' + prefixes[1] if len(prefixes) > 1 else ''
                # NOTE: parenthesize(node) needs an unparent node, so give it a clone:
                new_node = parenthesize(assert_arg_test_node.clone())
                new_node.prefix = prefixes[0] or ' '
                assert_arg_test_node.replace(new_node)

            self.__handle_opt_msg(assert_args, results)

            dest_tree.prefix = node.prefix
            return dest_tree

        else:
            return node

    @override_required
    def _transform_dest(self, assert_arg_test_node: PyNode, results: {str: PyNode}) -> bool:
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
            if len(msg.children) > 1:
                # the message text might have been passed by name, extract the text:
                children = msg.children
                if children[0] == PyLeaf(token.NAME, 'msg') and children[1] == PyLeaf(token.EQUAL, '='):
                    msg = children[2]

            msg = msg.clone()
            msg.prefix = ' '
            siblings = assertion_args_node.children
            siblings.append(PyLeaf(token.COMMA, ','))
            siblings.append(msg)


class FixAssert1Arg(FixAssertBase):
    """
    Fixer class for any 1-argument assertion function (assert_func(a)). It supports optional 2nd arg for the
    assertion message, ie assert_func(a, msg) -> assert a binop something, msg.
    """

    PATTERN = PATTERN_1_OR_2_ARGS

    # the path to arg node is different for every conversion
    # Example: assert_false(a) becomes "assert not a", so the PyNode for assertion expression is 'not a', and
    # the 'a' is its children[1] so self._arg_paths needs to be 1.
    conversions = dict(
        assert_true=('a', None),
        ok_=('a', None),
        assert_false=('not a', 1),
        assert_is_none=('a is None', 0),
        assert_is_not_none=('a is not None', 0),
    )

    @override(FixAssertBase)
    def _transform_dest(self, assert_arg_test_node: PyNode, results: {str: PyNode}) -> bool:
        test = results["test"]
        test = test.clone()
        if test.type == GENERATOR_TYPE:
            test = parenthesize(test)
        test.prefix = " "

        # the destination node for 'a' is in conv_data:
        dest_node = self._get_node(assert_arg_test_node, self._arg_paths)
        dest_node.replace(test)

        return True


class FixAssert2Args(FixAssertBase):
    """
    Fixer class for any 2-argument assertion function (assert_func(a, b)). It supports optional third arg
    as the assertion message, ie assert_func(a, b, msg) -> assert a binop b, msg.
    """

    PATTERN = PATTERN_2_OR_3_ARGS

    NEED_ARGS_PARENS = False

    # The args node paths are different for every conversion so the second item of each pair is paths infom
    # per base class. Here the paths info is itself a pair, one for arg a and the other for arg b.
    #
    # Example: assert_is_instance(a, b) converts to "assert isinstance(a, b)" so the conversion data is
    # the pair of node paths (1, 1, 0) and (1, 1, 1) since from the PyNode for the assertion expression
    # "isinstance(a, b)", 'a' is that node's children[1].children[1].children[0], whereas 'b' is
    # that node's children[1].children[1].children[1].
    conversions = dict(
        assert_is_instance=('isinstance(a, b)', ((1, 1, 0), (1, 1, 2))),
        assert_count_equal=('collections.Counter(a) == collections.Counter(b)', ((0, 2, 1), (2, 2, 1))),
        assert_not_regex=('not re.search(b, a)', ((1, 2, 1, 2), (1, 2, 1, 0))),
        assert_regex=('re.search(b, a)', ((2, 1, 2), (2, 1, 0))),
    )

    @override(FixAssertBase)
    def _transform_dest(self, assert_arg_test_node: PyNode, results: {str: PyNode}) -> bool:
        lhs = results["lhs"].clone()

        rhs = results["rhs"]
        rhs = rhs.clone()

        dest1 = self._get_node(assert_arg_test_node, self._arg_paths[0])
        dest2 = self._get_node(assert_arg_test_node, self._arg_paths[1])

        new_lhs = wrap_parens_for_comparison(lhs) if self.NEED_ARGS_PARENS else lhs
        dest1.replace(new_lhs)
        adjust_prefix_first_arg(new_lhs, results["lhs"].prefix)

        new_rhs = wrap_parens_for_comparison(rhs) if self.NEED_ARGS_PARENS else rhs
        dest2.replace(new_rhs)
        if get_prev_sibling(new_rhs).type in NEWLINE_OK_TOKENS:
            new_rhs.prefix = ''

        return True


class FixAssertBinOp(FixAssert2Args):
    """
    Fixer class for any 2-argument assertion function (assert_func(a, b)) that is of the form "a binop b".
    """

    NEED_ARGS_PARENS = True

    # The args node paths are the same for every binary comparison assertion: the first element is for
    # arg a, the second for arg b
    #
    # Example 1: assert_equal(a, b) will convert to "assert a == b" so the PyNode for assertion expression
    # is 'a == b' and a is that node's children[0], whereas b is that node's children[2], so the self._arg_paths
    # will be simply (0, 2).
    DEFAULT_ARG_PATHS = (0, 2)

    conversions = dict(
        assert_equal='a == b',
        eq_='a == b',
        assert_equals='a == b',
        assert_not_equal='a != b',

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


class FixAssertAlmostEq(FixAssertBase):
    """
    Fixer class for any 3-argument assertion function (assert_func(a, b, c)). It supports optional fourth arg
    as the assertion message, ie assert_func(a, b, c, msg) -> assert a op b op c, msg.
    """

    PATTERN = PATTERN_ALMOST_ARGS

    # The args node paths are the same for every assert function: the first tuple is for
    # arg a, the second for arg b, the third for arg c (delta).
    DEFAULT_ARG_PATHS = (0, (2, 2, 1, 0), (2, 2, 1, 2, 2))

    conversions = dict(
        assert_almost_equal='a == pytest.approx(b, abs=delta)',
        assert_not_almost_equal='a != pytest.approx(b, abs=delta)',
    )

    @override(FixAssertBase)
    def _transform_dest(self, assert_arg_test_node: PyNode, results: {str: PyNode}) -> bool:
        aaa = results["aaa"].clone()
        bbb = results["bbb"].clone()

        # first arg
        dest1 = self._get_node(assert_arg_test_node, self._arg_paths[0])
        new_aaa = wrap_parens_for_addsub(aaa)
        dest1.replace(new_aaa)
        adjust_prefix_first_arg(new_aaa, results["aaa"].prefix)

        # second arg
        dest2 = self._get_node(assert_arg_test_node, self._arg_paths[1])
        new_bbb = wrap_parens_for_addsub(bbb)
        if get_prev_sibling(dest2).type in NEWLINE_OK_TOKENS:
            new_bbb.prefix = ''
        dest2.replace(new_bbb)

        # third arg (optional)
        dest3 = self._get_node(assert_arg_test_node, self._arg_paths[2])

        if "arg3" not in results:
            # then only 2 args so `places` defaults to '7', delta to None and 'msg' to "":
            self._use_places_default(dest3)
            return True

        # NOTE: arg3 could be places or delta, or even msg
        arg3 = results["arg3"].clone()
        if "arg4" not in results:
            if arg3.children[0] == PyLeaf(token.NAME, 'msg'):
                self._fix_results_err_msg_arg(results, arg3)
                self._use_places_default(dest3)
                return True

            return self._process_if_arg_is_places_or_delta(arg3, dest3)

        # we have 4 args: msg could be last, or it could be third:
        # first try assuming 3rd arg is places/delta:
        if self._process_if_arg_is_places_or_delta(arg3, dest3):
            self._fix_results_err_msg_arg(results, results["arg4"].clone())
            return True

        # arg3 was not places/delta, try msg:
        if arg3.children[0] == PyLeaf(token.NAME, 'msg'):
            self._fix_results_err_msg_arg(results, arg3)
            delta_or_places = results["arg4"].clone()
            return self._process_if_arg_is_places_or_delta(delta_or_places, dest3)

        else:
            # if arg4 name is not msg, no match:
            return False

    def _use_places_default(self, abs_dest: PyNode):
        places_node = PyLeaf(token.NUMBER, '7', prefix="1e-")
        abs_dest.replace(places_node)

    def _fix_results_err_msg_arg(self, results: {str: PyNode}, err_msg_node: PyNode):
        # caller will look for 'msg' not 'arg3' so fix this:
        err_msg_node.children[2].prefix = ""
        results['msg'] = err_msg_node  # the caller will look for this

    def _process_if_arg_is_places_or_delta(self, arg3: PyNode, dest3: PyNode) -> bool:
        if arg3.children[0] == PyLeaf(token.NAME, 'delta'):
            arg3_val = arg3.children[2]
            arg3_val.prefix = ""
            wrapped_delta_val = wrap_parens_for_comparison(arg3_val)
            dest3.replace(wrapped_delta_val)

        elif arg3.children[0] == PyLeaf(token.NAME, 'places'):
            arg3_val = arg3.children[2]
            arg3_val.prefix = "1e-"
            wrapped_places_val = wrap_parens_for_comparison(arg3_val)
            dest3.replace(wrapped_places_val)

        else:
            return False

        return True


# ------------ Main portion of script -------------------------------

class NoseConversionRefactoringTool(refactor.MultiprocessRefactoringTool):
    def __init__(self, verbose: bool = False):
        flags = dict(print_function=True)
        super().__init__([], flags)
        level = logging.DEBUG if verbose else logging.INFO
        logging.basicConfig(format='%(name)s: %(message)s', level=level)
        logger = logging.getLogger('fissix.main')

    def get_fixers(self):
        pre_fixers = []
        post_fixers = []

        pre_fixers.extend(FixAssert1Arg.create_all(self.options, self.fixer_log))
        pre_fixers.extend(FixAssert2Args.create_all(self.options, self.fixer_log))
        pre_fixers.extend(FixAssertBinOp.create_all(self.options, self.fixer_log))
        pre_fixers.extend(FixAssertAlmostEq.create_all(self.options, self.fixer_log))

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
    parser.add_argument('-v', dest='verbose', action='store_true',
                        help='verbose output (list files changed, etc)')
    parser.add_argument('--version', action='version',
                        version='%(prog)s {0}'.format(__version__))

    return parser.parse_args()


def main():
    args = setup()
    if not Path(args.dir_name).exists():
        print('ERROR: Path "%s" does not exist' % args.dir_name, file=sys.stderr)
        sys.exit(1)

    refac = NoseConversionRefactoringTool(args.verbose)
    refac.refactor_dir(args.dir_name, write=args.write)


if __name__ == '__main__':
    main()

__license__ = """
    Copyright (c) 2016, Oliver Schoenborn
    All rights reserved.

    Redistribution and use in source and binary forms, with or without
    modification, are permitted provided that the following conditions are met:

    * Redistributions of source code must retain the above copyright notice, this
      list of conditions and the following disclaimer.

    * Redistributions in binary form must reproduce the above copyright notice,
      this list of conditions and the following disclaimer in the documentation
      and/or other materials provided with the distribution.

    * Neither the name of nose2pytest nor the names of its
      contributors may be used to endorse or promote products derived from
      this software without specific prior written permission.

    THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
    AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
    IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
    DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
    FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
    DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
    SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
    CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
    OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
    OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""
