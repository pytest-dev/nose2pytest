import logging
from logging import StreamHandler
import sys
from textwrap import dedent
import pytest

from nose2pytest import FixAssert1ArgAopB, FixAssert2ArgsAopB, NoseConversionRefactoringTool


log = logging.getLogger('nose2pytest')

nosetools = {}


@pytest.fixture(scope="session", autouse=True)
def setup_log():
    redirect = StreamHandler(stream=sys.stdout)
    redirect.setLevel(logging.DEBUG)
    log.addHandler(redirect)
    log.setLevel(logging.DEBUG)

    import nose.tools
    global nosetools
    for name, val in vars(nose.tools).items():
        if name.startswith('assert_'):
            nosetools[name] = val


class Test1Arg:

    def test_params(self):
        test_script = dedent("""
            log.print("hi")

            assert_true(a)
            assert_true(a, msg)
            assert_true(a, msg='text')
            """)

        refac = NoseConversionRefactoringTool()
        result = refac.refactor_string(test_script, 'script')
        assert str(result) == dedent("""
            log.print("hi")

            assert a
            assert a, msg
            assert a, msg='text'
            """)

    def __check_passes(self, refac, statement_in):
        result = refac.refactor_string(statement_in + '\n', 'script')
        statement_out = str(result)
        exec(statement_in, nosetools)
        exec(statement_out)

    def __check_fails(self, refac, statement_in):
        result = refac.refactor_string(statement_in + '\n', 'script')
        statement_out = str(result)
        pytest.raises(AssertionError, exec, statement_in, nosetools)
        pytest.raises(AssertionError, exec, statement_out)

    def test_true(self):
        refac = NoseConversionRefactoringTool()

        statement_in = 'assert_true(True)'
        self.__check_passes(refac, statement_in)

        statement_in = 'assert_true(False)'
        self.__check_fails(refac, statement_in)

    def test_false(self):
        pass

    def test_is_none(self):
        pass

    def test_is_not_none(self):
        pass


class Test2Args:

    def test_2(self):
        test_script = dedent("""
            assert_in(a, b)
            assert_in(a, b, text)
            assert_in(a, b, msg='text')
            assert_in(a in c, b in c)
            """)

        refac = NoseConversionRefactoringTool()
        result = refac.refactor_string(test_script, 'script')
        assert str(result) == dedent("""
            assert a in b
            assert a in b, text
            assert a in b, msg='text'
            assert (a in c) in (b in c)
            """)

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

        refac = NoseConversionRefactoringTool()
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

    def test_binops(self):
        redirect = StreamHandler(stream=sys.stdout)
        redirect.setLevel(logging.DEBUG)
        log.addHandler(redirect)
        log.setLevel(logging.DEBUG)

        test_script = dedent("""
            assert_in(long_a,
                      long_b)
            """)

        for key in FixAssert1ArgAopB.conversions:
            test_script += '{}(123)\n'.format(key)
        for key in FixAssert2ArgsAopB.conversions:
            test_script += '{}(123, 456)\n'.format(key)
        log.info(test_script)

        refac = NoseConversionRefactoringTool()
        result = refac.refactor_string(test_script, 'script')
        side_by_side = (('{} -> {}'.format(a, b) if a else '')
                        for a, b in zip(test_script.split('\n'), str(result).split('\n')))
        log.info('\n'.join(side_by_side))

