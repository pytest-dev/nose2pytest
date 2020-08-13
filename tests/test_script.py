import logging
import sys
from logging import StreamHandler
from textwrap import dedent

import pytest

from nose2pytest.script import NoseConversionRefactoringTool
from nose2pytest.assert_tools import _supported_nose_name

log = logging.getLogger('nose2pytest')

nosetools = {}
pytesttools = {}

refac = NoseConversionRefactoringTool()


@pytest.fixture(scope="session", autouse=True)
def setup_log():
    redirect = StreamHandler(stream=sys.stdout)
    redirect.setLevel(logging.DEBUG)
    log.addHandler(redirect)
    log.setLevel(logging.DEBUG)

    import nose.tools
    for name, val in vars(nose.tools).items():
        if _supported_nose_name(name):
            nosetools[name] = val

    import re, collections
    pytesttools['re'] = re
    pytesttools['collections'] = collections


def check_transformation(input, expect):
    result = refac.refactor_string(dedent(input + '\n'), 'script')
    assert dedent(expect + '\n') == str(result)


def check_passes(refac, statement_in, expect_out):
    result = refac.refactor_string(statement_in + '\n', 'script')
    statement_out = str(result)
    exec(statement_in, nosetools)
    exec(statement_out, pytesttools)
    assert statement_out == expect_out + '\n'


def check_fails(refac, statement_in, expect_out):
    result = refac.refactor_string(statement_in + '\n', 'script')
    statement_out = str(result)
    pytest.raises(AssertionError, exec, statement_in, nosetools)
    pytest.raises(AssertionError, exec, statement_out, pytesttools)
    assert statement_out == expect_out + '\n'


class Test1Arg:

    def test_params(self):
        test_script = """
            log.print("hi")

            assert_true(a)
            ok_(a)
            assert_true(a, 'text')
            assert_true(a, msg='text')
            """
        check_transformation(test_script, """
            log.print("hi")

            assert a
            assert a
            assert a, 'text'
            assert a, 'text'
            """)

    def test_parens(self):
        check_transformation('assert_true(a + \nb)', 'assert (a + \nb)')

    def test_generator(self):
        check_transformation('assert_true(x for x in range(1))', 'assert (x for x in range(1))')

    def test_same_results(self):
        check_passes(refac, 'assert_true(True)', 'assert True')
        check_fails(refac, 'assert_true(False)', 'assert False')

        check_passes(refac, 'ok_(True)', 'assert True')
        check_fails(refac, 'ok_(False)', 'assert False')

        check_passes(refac, 'assert_false(False)', 'assert not False')
        check_fails(refac, 'assert_false(True)', 'assert not True')

        check_passes(refac, 'assert_is_none(None)', 'assert None is None')
        check_fails(refac, 'assert_is_none("")', 'assert "" is None')

        check_passes(refac, 'assert_is_not_none("")', 'assert "" is not None')
        check_fails(refac, 'assert_is_not_none(None)', 'assert None is not None')


class Test2Args:

    def test_params(self):
        test_script = """
            assert_in(a, b)
            assert_in(a, b, 'text')
            assert_in(a, b, msg='text')
            """
        check_transformation(test_script, """
            assert a in b
            assert a in b, 'text'
            assert a in b, 'text'
            """)

    def test_dont_add_parens(self):
        check_transformation('assert_in(a, c)',
                             'assert a in c')
        check_transformation('assert_in(a.b, c)',
                             'assert a.b in c')
        check_transformation('assert_in(a.b(), c)',
                             'assert a.b() in c')
        check_transformation('assert_in(a(), d)',
                             'assert a() in d')
        check_transformation('assert_in(a[1], d)',
                             'assert a[1] in d')
        check_transformation('assert_in((a+b), d)',
                             'assert (a+b) in d')
        check_transformation('assert_in((a+b), d)',
                             'assert (a+b) in d')
        check_transformation('assert_in(-a, +b)',
                             'assert -a in +b')

    def test_add_parens(self):
        check_transformation('assert_in(a == b, d)',
                             'assert (a == b) in d')
        check_transformation('assert_in(a != b, d)',
                             'assert (a != b) in d')
        check_transformation('assert_in(b <= c, d)',
                             'assert (b <= c) in d')
        check_transformation('assert_in(c >= d, d)',
                             'assert (c >= d) in d')
        check_transformation('assert_in(d < e, d)',
                             'assert (d < e) in d')
        check_transformation('assert_in(d > e, d)',
                             'assert (d > e) in d')
        check_transformation('eq_(a in b, c)',
                             'assert (a in b) == c')
        check_transformation('assert_equal(a in b, c)',
                             'assert (a in b) == c')
        check_transformation('assert_equal(a not in b, c)',
                             'assert (a not in b) == c')
        check_transformation('assert_equal(a is b, c)',
                             'assert (a is b) == c')
        check_transformation('assert_equal(a is not b, c)',
                             'assert (a is not b) == c')
        check_transformation('assert_equal(not a, c)',
                             'assert (not a) == c')
        check_transformation('assert_equal(a and b, c or d)',
                             'assert (a and b) == (c or d)')
        check_transformation('assert_in(a.b + c, d)',
                             'assert a.b + c in d')
        check_transformation('assert_in(a() + b, d)',
                             'assert a() + b in d')
        check_transformation('assert_in(a + b, c + d)',
                             'assert a + b in c + d')
        check_transformation('assert_in(a + b, c + d, "text")',
                             'assert a + b in c + d, "text"')
        check_transformation('assert_equal(a + b if c + d < 0 else e + f if g+h < 0 else i + j, -100)',
                             'assert (a + b if c + d < 0 else e + f if g+h < 0 else i + j) == -100')

    def test_newline_all(self):
        test_script = """
            assert_in(long_a,
                      long_b)
        """
        check_transformation(test_script, """
            assert (long_a in
                      long_b)
        """)

        test_script = """
            assert_in(
                long_a, long_b)
        """
        check_transformation(test_script, """
            assert (
                long_a in long_b)
        """)

        test_script = """
            assert_in(long_a,
                      long_b + something)
        """
        check_transformation(test_script, """
            assert (long_a in
                      long_b + something)
        """)

        test_script = """
            assert_in(long_a,
                      long_b > something)
        """
        check_transformation(test_script, """
            assert (long_a in
                      (long_b > something))
        """)

        test_script = """
            assert_in(a, long_b +
                         something)
        """
        check_transformation(test_script, """
            assert (a in long_b +
                         something)
        """)

    def test_same_results(self):
        check_passes(refac, 'assert_equal(123, 123)', 'assert 123 == 123')
        check_fails(refac,  'assert_equal(123, 456)', 'assert 123 == 456')
        check_passes(refac, 'assert_equals(123, 123)', 'assert 123 == 123')
        check_fails(refac,  'assert_equals(123, 456)', 'assert 123 == 456')
        check_passes(refac, 'eq_(123, 123)', 'assert 123 == 123')
        check_fails(refac,  'eq_(123, 456)', 'assert 123 == 456')

        check_passes(refac, 'assert_not_equal(123, 456)', 'assert 123 != 456')
        check_fails(refac,  'assert_not_equal(123, 123)', 'assert 123 != 123')
        check_passes(refac, 'assert_not_equals(123, 456)', 'assert 123 != 456')
        check_fails(refac,  'assert_not_equals(123, 123)', 'assert 123 != 123')

        check_passes(refac, 'assert_list_equal([123, 456], [123, 456])', 'assert [123, 456] == [123, 456]')
        check_fails(refac,  'assert_list_equal([123, 123], [123, 456])', 'assert [123, 123] == [123, 456]')

        check_passes(refac, 'assert_tuple_equal((123, 456), (123, 456))', 'assert (123, 456) == (123, 456)')
        check_fails(refac,  'assert_tuple_equal((123, 123), (123, 456))', 'assert (123, 123) == (123, 456)')

        check_passes(refac, 'assert_set_equal({123, 456}, {123, 456})', 'assert {123, 456} == {123, 456}')
        check_fails(refac,  'assert_set_equal({123, 123}, {123, 456})', 'assert {123, 123} == {123, 456}')

        check_passes(refac, 'assert_dict_equal(dict(a=123, b=456), dict(a=123, b=456))', 'assert dict(a=123, b=456) == dict(a=123, b=456)')
        check_fails(refac,  'assert_dict_equal(dict(a=123, b=456), dict(a=123, b=123))', 'assert dict(a=123, b=456) == dict(a=123, b=123)')
        check_fails(refac,  'assert_dict_equal(dict(a=123, b=456), dict(a=123, c=456))', 'assert dict(a=123, b=456) == dict(a=123, c=456)')

        check_passes(refac, 'assert_multi_line_equal("""1\n2\n""", """1\n2\n""")', 'assert """1\n2\n""" == """1\n2\n"""')
        check_fails(refac,  'assert_multi_line_equal("""1\n2\n""", """1\n3\n""")', 'assert """1\n2\n""" == """1\n3\n"""')

        check_passes(refac, 'assert_greater(123, 1)',   'assert 123 > 1'  )
        check_fails(refac,  'assert_greater(123, 123)', 'assert 123 > 123')
        check_fails(refac,  'assert_greater(123, 456)', 'assert 123 > 456')

        check_passes(refac, 'assert_greater_equal(123, 1)',   'assert 123 >= 1'  )
        check_passes(refac, 'assert_greater_equal(123, 123)', 'assert 123 >= 123')
        check_fails(refac,  'assert_greater_equal(123, 456)', 'assert 123 >= 456')

        check_passes(refac, 'assert_less(123, 456)', 'assert 123 < 456')
        check_fails(refac,  'assert_less(123, 123)', 'assert 123 < 123')
        check_fails(refac,  'assert_less(123, 1)',   'assert 123 < 1'  )

        check_passes(refac, 'assert_less_equal(123, 456)', 'assert 123 <= 456')
        check_passes(refac, 'assert_less_equal(123, 123)', 'assert 123 <= 123')
        check_fails(refac,  'assert_less_equal(123, 1)'  , 'assert 123 <= 1'  )

        check_passes(refac, 'assert_in(123, [123, 456])', 'assert 123 in [123, 456]')
        check_fails(refac,  'assert_in(123, [789, 456])', 'assert 123 in [789, 456]')

        check_passes(refac, 'assert_not_in(123, [789, 456])', 'assert 123 not in [789, 456]')
        check_fails(refac,  'assert_not_in(123, [123, 456])', 'assert 123 not in [123, 456]')

        check_passes(refac, 'assert_is(123, 123)', 'assert 123 is 123')
        check_fails(refac,  'assert_is(123, 1)', 'assert 123 is 1')

        check_passes(refac, 'assert_is_not(123, 1)', 'assert 123 is not 1')
        check_fails(refac,  'assert_is_not(123, 123)', 'assert 123 is not 123')

        check_passes(refac, 'assert_is_instance(123, int)', 'assert isinstance(123, int)')
        check_fails(refac,  'assert_is_instance(123, float)', 'assert isinstance(123, float)')

        check_passes(refac, 'assert_count_equal([456, 789, 456], [456, 456, 789])',
                     'assert collections.Counter([456, 789, 456]) == collections.Counter([456, 456, 789])')
        check_fails(refac,  'assert_count_equal([789, 456], [456])',
                    'assert collections.Counter([789, 456]) == collections.Counter([456])')

        check_passes(refac, 'assert_regex("125634", "12.*34")', 'assert re.search("12.*34","125634")')
        check_fails(refac,  'assert_regex("125678", "12.*34")', 'assert re.search("12.*34","125678")')

        check_passes(refac, 'assert_not_regex("125678", "12.*34")', 'assert not re.search("12.*34","125678")')
        check_fails(refac,  'assert_not_regex("125634", "12.*34")', 'assert not re.search("12.*34","125634")')


class Test3Args:

    def test_no_add_parens(self):
        check_transformation('assert_almost_equal(a * b, ~c, delta=d**e)', 'assert abs(a * b - ~c) <= d**e')

    def test_add_parens(self):
        check_transformation('assert_almost_equal(a + b, c, delta=d>e)', 'assert abs((a + b) - c) <= (d>e)')
        check_transformation('assert_almost_equal(a | b, c ^ d, delta=0.1)', 'assert abs((a | b) - (c ^ d)) <= 0.1')
        check_transformation('assert_almost_equal(a & b, c << d, delta=0.1)', 'assert abs((a & b) - (c << d)) <= 0.1')
        check_transformation('assert_almost_equal(a or b, c >> d, delta=0.1)', 'assert abs((a or b) - (c >> d)) <= 0.1')

    def test_almost_equal(self):
        check_passes(refac, 'assert_almost_equal(123.456, 123.5, delta=0.1)', 'assert abs(123.456 - 123.5) <= 0.1')
        check_passes(refac, 'assert_almost_equal(123.456, 123.5, delta=0.2, msg="text")', 'assert abs(123.456 - 123.5) <= 0.2, "text"')
        check_passes(refac, 'assert_almost_equal(123.456, 123.5, msg="text", delta=0.3)', 'assert abs(123.456 - 123.5) <= 0.3, "text"')
        check_fails(refac,  'assert_almost_equal(123.456, 124, delta=0.1)', 'assert abs(123.456 - 124) <= 0.1')

        check_passes(refac, 'assert_almost_equals(123.456, 123.5, delta=0.1)', 'assert abs(123.456 - 123.5) <= 0.1')
        check_passes(refac, 'assert_almost_equals(123.456, 123.5, delta=0.2, msg="text")', 'assert abs(123.456 - 123.5) <= 0.2, "text"')
        check_passes(refac, 'assert_almost_equals(123.456, 123.5, msg="text", delta=0.3)', 'assert abs(123.456 - 123.5) <= 0.3, "text"')
        check_fails(refac, 'assert_almost_equals(123.456, 124, delta=0.1)', 'assert abs(123.456 - 124) <= 0.1')

        check_passes(refac, 'assert_not_almost_equal(123.456, 123.5, delta=0.01)', 'assert abs(123.456 - 123.5) > 0.01')
        check_passes(refac, 'assert_not_almost_equal(123.456, 123.5, delta=0.02, msg="text")', 'assert abs(123.456 - 123.5) > 0.02, "text"')
        check_passes(refac, 'assert_not_almost_equal(123.456, 123.5, msg="text", delta=0.03)', 'assert abs(123.456 - 123.5) > 0.03, "text"')
        check_fails(refac,  'assert_not_almost_equal(123.456, 124, delta=0.6)', 'assert abs(123.456 - 124) > 0.6')

        check_passes(refac, 'assert_not_almost_equals(123.456, 123.5, delta=0.01)', 'assert abs(123.456 - 123.5) > 0.01')
        check_passes(refac, 'assert_not_almost_equals(123.456, 123.5, delta=0.02, msg="text")', 'assert abs(123.456 - 123.5) > 0.02, "text"')
        check_passes(refac, 'assert_not_almost_equals(123.456, 123.5, msg="text", delta=0.03)', 'assert abs(123.456 - 123.5) > 0.03, "text"')
        check_fails(refac,  'assert_not_almost_equals(123.456, 124, delta=0.6)', 'assert abs(123.456 - 124) > 0.6')

    def test_ignore_places(self):
        statement_in = 'assert_almost_equal(123.456, 123.5, 2)'
        check_transformation(statement_in, statement_in)

        statement_in = 'assert_almost_equal(123.456, 123.5, places=2)'
        check_transformation(statement_in, statement_in)


class TestAssertTools:

    def test_almost(self):
        from pytest import assert_almost_equal, assert_not_almost_equal

        assert_almost_equal(1, 1.00001, 4)
        assert_not_almost_equal(1, 1.01, 3)
        pytest.raises(AssertionError, assert_almost_equal, 1, 1.01, 5)
        pytest.raises(AssertionError, assert_not_almost_equal, 1, 1.00001, 2)
        # assert_almost_equal(1, 1.01, 5)
        # assert_not_almost_equal(1, 1.00001, 2)

    def test_dict_keys_subset(self):
        dict1 = dict(a=1, b=2, c=3)

        # check keys are subset:
        dict2 = dict1.copy()
        pytest.assert_dict_contains_subset(dict1, dict2)

        dict2['d'] = 4
        pytest.assert_dict_contains_subset(dict1, dict2)

        del dict2['a']
        pytest.raises(AssertionError, pytest.assert_dict_contains_subset, dict1, dict2)
        # assert_dict_contains_subset(dict1, dict2)

    def test_dict_values_subset(self):
        dict1 = dict(a=1, b=2, c=3)

        # check keys are subset:
        dict2 = dict1.copy()
        dict2['d'] = 4
        dict2['a'] = 4
        pytest.raises(AssertionError, pytest.assert_dict_contains_subset, dict1, dict2)
        # assert_dict_contains_subset(dict1, dict2)
