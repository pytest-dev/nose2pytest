from setuptools import setup


setup(
        name='nose2pytest',
        version='1.0.8',
        packages=['nose2pytest'],
        # py_modules=['assert_tools', 'nose2pytest'],
        entry_points={
            'console_scripts': [
                'nose2pytest = nose2pytest.script:main',
            ],
            'pytest11': ['pytest_nose_assert_tools = nose2pytest.assert_tools'],
        },
        url='https://github.com/schollii/nose2pytest',
        license='BSD-3',
        author='Oliver Schoenborn',
        author_email='oliver.schoenborn@gmail.com',
        description='Convert nose.tools.assert_ calls found in your Nose test modules into raw asserts for pytest',
        keywords='nose to pytest conversion',

        python_requires='>=3.5',
        classifiers=[
            # How mature is this project? Common values are
            #   3 - Alpha
            #   4 - Beta
            #   5 - Production/Stable
            'Development Status :: 5 - Production/Stable',

            # Indicate who your project is intended for
            'Intended Audience :: Developers',
            'Topic :: Software Development :: Testing',

            # Pick your license as you wish (should match "license" above)
            'License :: OSI Approved :: BSD License',

            # Specify the Python versions you support here.
            'Programming Language :: Python :: 3',
            'Programming Language :: Python :: 3 :: Only',
            'Programming Language :: Python :: 3.5',
            'Programming Language :: Python :: 3.6',
            'Programming Language :: Python :: 3.7',
            'Programming Language :: Python :: 3.8',
        ],
)
