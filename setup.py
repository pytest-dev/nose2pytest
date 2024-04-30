from setuptools import setup


setup(
        name='nose2pytest',
        version='1.0.12',
        packages=['nose2pytest'],
        long_description=open('README.rst', encoding="UTF-8").read(),
        long_description_content_type="text/x-rst",
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
        install_requires=[
            'fissix',
        ],
        python_requires='>=3.8,<3.12',
        classifiers=[
            'Development Status :: 5 - Production/Stable',

            # Indicate who your project is intended for
            'Intended Audience :: Developers',
            'Topic :: Software Development :: Testing',

            # Pick your license as you wish (should match "license" above)
            'License :: OSI Approved :: BSD License',

            # Specify the Python versions you support here.
            'Programming Language :: Python :: 3.8',
            'Programming Language :: Python :: 3.9',
            'Programming Language :: Python :: 3.10',
            'Programming Language :: Python :: 3.11',
        ],
)
