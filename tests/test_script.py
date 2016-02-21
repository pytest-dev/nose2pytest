import logging
from logging import StreamHandler
import sys
from textwrap import dedent
import pytest

from nose2pytest import FixAssert1Arg, FixAssert2Args, NoseConversionRefactoringTool


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
        if name.startswith('assert_'):
            nosetools[name] = val

    import re, collections
    pytesttools['re'] = re
    pytesttools['collections'] = collections


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
        test_script = dedent("""
            log.print("hi")

            assert_true(a)
            assert_true(a, 'text')
            assert_true(a, msg='text')
            """)

        result = refac.refactor_string(test_script, 'script')
        assert str(result) == dedent("""
            log.print("hi")

            assert a
            assert a, 'text'
            assert a, 'text'
            """)

    def test_parens(self):
        result = refac.refactor_string('assert_true(a + \nb)\n', 'script')
        assert str(result) == 'assert (a + \nb)\n'

    def test_same_results(self):
        check_passes(refac, 'assert_true(True)', 'assert True')
        check_fails(refac, 'assert_true(False)', 'assert False')

        check_passes(refac, 'assert_false(False)', 'assert not False')
        check_fails(refac, 'assert_false(True)', 'assert not True')

        check_passes(refac, 'assert_is_none(None)', 'assert None is None')
        check_fails(refac, 'assert_is_none("")', 'assert "" is None')

        check_passes(refac, 'assert_is_not_none("")', 'assert "" is not None')
        check_fails(refac, 'assert_is_not_none(None)', 'assert None is not None')


class Test2Args:

    def test_params(self):
        test_script = dedent("""
            assert_in(a, b)
            assert_in(a, b, 'text')
            assert_in(a, b, msg='text')
            """)

        result = refac.refactor_string(test_script, 'script')
        assert str(result) == dedent("""
            assert a in b
            assert a in b, 'text'
            assert a in b, 'text'
            """)

    def test_parens(self):
        result = refac.refactor_string('assert_in(a + b, c + d)\n', 'script')
        assert str(result) == 'assert (a + b) in (c + d)\n'

        result = refac.refactor_string('assert_in(a + b, c + d, "text")\n', 'script')
        assert str(result) == 'assert (a + b) in (c + d), "text"\n'

    def test_newline(self):
        test_script = dedent("""
            assert_in(long_a,
                      long_b)

            assert_in(
                long_a, long_b)

            assert_in(a, long_b +
                         something)

            assert_in(long_a,
                      long_b + something)
            """)

        result = refac.refactor_string(test_script, 'script')
        assert str(result) == dedent("""
            assert (long_a in
                      long_b)

            assert (
                long_a in long_b)

            assert a in (long_b +
                         something)

            assert (long_a in
                      (long_b + something))
            """)

    def test_same_results(self):
        check_passes(refac, 'assert_equal(123, 123)', 'assert 123 == 123')
        check_fails(refac,  'assert_equal(123, 456)', 'assert 123 == 456')
        check_passes(refac, 'assert_equals(123, 123)', 'assert 123 == 123')
        check_fails(refac,  'assert_equals(123, 456)', 'assert 123 == 456')

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

    def test_almost_equal(self):
        check_passes(refac, 'assert_almost_equal(123.456, 123.5, delta=0.1)', 'assert abs(123.456 - 123.5) <= 0.1')
        check_passes(refac, 'assert_almost_equal(123.456, 123.5, delta=0.2, msg="text")', 'assert abs(123.456 - 123.5) <= 0.2, "text"')
        check_passes(refac, 'assert_almost_equal(123.456, 123.5, msg="text", delta=0.3)', 'assert abs(123.456 - 123.5) <= 0.3, "text"')
        check_fails(refac, 'assert_almost_equal(123.456, 124, delta=0.1)', 'assert abs(123.456 - 124) <= 0.1')

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
        statement_in = 'assert_almost_equal(123.456, 123.5, 2)\n'
        result = refac.refactor_string(statement_in, 'script')
        assert str(result) == statement_in

        statement_in = 'assert_almost_equal(123.456, 123.5, places=2)\n'
        result = refac.refactor_string(statement_in, 'script')
        assert str(result) == statement_in


