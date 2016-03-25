from setuptools import setup


setup(
        name='nose2pytest',
        version='1.0.0',
        packages=[],
        py_modules=['assert_tools',],
        scripts=['nose2pytest.py'],
        url='https://github.com/schollii/nose2pytest',
        license='BSD-3',
        author='Oliver Schoenborn',
        author_email='oliver.schoenborn@gmail.com',
        description='Convert nose.tools.assert_ calls found in your Nose test modules into raw asserts for pytest',
        keywords='nose pytest conversion',

        classifiers=[
            # How mature is this project? Common values are
            #   3 - Alpha
            #   4 - Beta
            #   5 - Production/Stable
            'Development Status :: 4 - beta',

            # Indicate who your project is intended for
            'Intended Audience :: Developers',
            'Topic :: Software Development :: Testing',

            # Pick your license as you wish (should match "license" above)
            'License :: OSI Approved :: BSD License',

            # Specify the Python versions you support here. In particular, ensure
            # that you indicate whether you support Python 2, Python 3 or both.
            'Programming Language :: Python :: 3.4',
        ],
)
