"""
Convert nose assertions to pytest

Automaticlly converts all assert_ functions -> assert, except that:

These must be done manually via search-replace:
- @raises\((.*)\) -> can try @pytest.mark.xfail(raises=$1) but I prefer to convert test to use pytest.raises
  in test function body
- assert_is_instance -> assert isinstance
- assert_raises -> pytest.raises
- assert_warns -> pytest.warns

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

These will stay and you may have to re-implement if you want to remove any nose dependencies:
- assert_dict_contains_subset(a,b) -> assert set(b.keys()) >= a.keys() and {k: b[k] for k in a if k in b} == a
- assert_logs
- assert_raises_regex
- assert_raises_regexp  # deprecated
- assert_regexp_matches # deprecated
- assert_warns_regex
"""
from lib2to3 import refactor, fixer_base, pygram, pytree, pgen2
import logging

# FIXER:


class FixAssertBase(fixer_base.BaseFix):
    # BM_compatible = True

    def __init__(self, nose_func, pytest_func, *args, **kwargs):
        self.PATTERN = self.PATTERN.format(nose_func)
        super().__init__(*args, **kwargs)

        grammar = pygram.python_grammar
        logger = logging.getLogger("NoseConversionTool")
        driver = pgen2.driver.Driver(grammar, convert=pytree.convert, logger=logger)
        self.dest_tree = driver.parse_string(pytest_func + '\n')
        # remove the \n we added
        del self.dest_tree.children[0].children[1]

        print('added ', self.__class__)

    def transform(self, node, results):
        assert results
        dest_tree = self.dest_tree.clone()
        self._transform_dest(dest_tree, results)
        dest_tree.prefix = node.prefix
        return dest_tree


class FixAssert1Arg(FixAssertBase):

    PATTERN = """
    power< '{}'
        trailer<
            '('
            obj1=any
            ')'
        >
    >
    """

    conversions = dict(
        assert_is_none='a is None',
        assert_is_not_none='a is not None',
    )

    def _transform_dest(self, dest_tree, results):
        obj1 = results["obj1"]
        obj1 = obj1.clone()
        obj1.prefix = " "

        node = dest_tree.children[0].children[0].children[1]
        node.children[0] = obj1


class FixAssertTrue(FixAssertBase):

    PATTERN = """
    power< 'assert_true'
        trailer<
            '('
            arglist<
                obj1=any
            >
            ')'
        >
    >
    """

    def _transform_dest(self, dest_tree, results):
        obj1 = results["obj1"]
        obj1 = obj1.clone()
        obj1.prefix = " "

        node = dest_tree.children[0].children[0].children[1]
        node.children[0] = obj1


class FixAssert2Args(FixAssertBase):

    PATTERN = """
    power< '{}'
        trailer<
            '('
            arglist<
                obj1=any ','
                obj2=any
            >
            ')'
        >
    >
    """

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

    def _transform_dest(self, dest_tree, results):
        obj1 = results["obj1"]
        obj1 = obj1.clone()
        obj1.prefix = " "
        obj2 = results["obj2"]
        obj2 = obj2.clone()

        node = dest_tree.children[0].children[0].children[1]
        node.children[0] = obj1
        node.children[2] = obj2


class NoseConversoinRefactoringTool(refactor.MultiprocessRefactoringTool):
    def __init__(self, flags):
        super().__init__([], flags)

    def get_fixers(self):
        pre_fixers = []

        for nose_func, pytest_func in FixAssert1Arg.conversions.items():
            pre_fixers.append(FixAssert1Arg(nose_func, 'assert ' + pytest_func, self.options, self.fixer_log))
        for nose_func, pytest_func in FixAssert2Args.conversions.items():
            pre_fixers.append(FixAssert2Args(nose_func, 'assert ' + pytest_func, self.options, self.fixer_log))

        return pre_fixers, []


from nose import tools
for key in dir(tools):
    if key.startswith('assert_'):
        print(key)

flags = dict(print_function = True)
refac = NoseConversoinRefactoringTool(flags)

test_script = """
log.print("hi")
assert_in(a, b, msg)
"""

for key in FixAssert1Arg.conversions:
    test_script += '{}(123)\n'.format(key)
for key in FixAssert2Args.conversions:
    test_script += '{}(123, 456)\n'.format(key)
print(test_script)

result = refac.refactor_string(test_script, 'script')
print(result)

# refac.refactor_file(r'test_console\test05_core\test05_logging.py', write=True)

