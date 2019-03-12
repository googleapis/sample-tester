import io
import os

from setuptools import find_packages, setup

PACKAGE_ROOT = os.path.abspath(os.path.dirname(__file__))

with io.open(os.path.join(PACKAGE_ROOT, 'README.md')) as file_obj:
    README = file_obj.read()

setup(
    name='sample-tester',
    version='0.7.7.1',

    license='Apache 2.0',
    author='Victor Chudnovsky',
    author_email='vchudnov+sampletester@google.com',
    url='https://github.com/googleapis/sample-tester',
    packages=find_packages(exclude=['docs', 'tests']),
    description=('Tool for testing semantically equivalent samples in multiple '
                 'languages and environments'),
    long_description=README,
    long_description_content_type='text/markdown',
    entry_points="""[console_scripts]
        sample-tester=sampletester.cli:main
    """,
    platforms='Posix; MacOS X',
    include_package_data=True,
    install_requires=(
        'pyyaml >= 5.1',
    ),

    classifiers=(
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: POSIX',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Software Development :: Code Generators',
    ),
)
