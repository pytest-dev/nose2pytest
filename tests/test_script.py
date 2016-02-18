import logging
from logging import StreamHandler
import sys
from textwrap import dedent
import pytest

from nose2pytest import FixAssert1ArgAopB, FixAssert2ArgsAopB, NoseConversionRefactoringTool


log = logging.getLogger('nose2pytest')


class Test1Arg:

    def test_1(self):
        redirect = StreamHandler(stream=sys.stdout)
        redirect.setLevel(logging.DEBUG)
        log.addHandler(redirect)
        log.setLevel(logging.DEBUG)

        test_script = dedent("""
            log.print("hi")

            assert_true(a)
            assert_true(a, msg)
            assert_true(a, msg='text')

            assert_in(a, b)
            assert_in(a, b, text)
            assert_in(a, b, msg='text')

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

