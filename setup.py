# Copyright 2019 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import io
import os

from setuptools import find_packages, setup

PACKAGE_ROOT = os.path.abspath(os.path.dirname(__file__))

with io.open(os.path.join(PACKAGE_ROOT, 'README.rst')) as file_obj:
    README = file_obj.read()

setup(
    name='sample-tester',
    version='0.9.0',

    license='Apache 2.0',
    author='Victor Chudnovsky',
    author_email='vchudnov+sampletester@google.com',
    url='https://github.com/googleapis/sample-tester',
    packages=find_packages(exclude=['docs', 'tests']),
    description=('Tool for testing semantically equivalent samples in multiple '
                 'languages and environments'),
    long_description=README,
    entry_points="""[console_scripts]
        sample-tester=sampletester.cli:main
    """,
    platforms='Posix; MacOS X',
    include_package_data=True,
    install_requires=(
        'pyyaml',
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
