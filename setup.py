# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CESNET.
#
# invenio-integration-tests is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""invenio integration tests"""

import os

from setuptools import find_packages, setup

readme = open('README.md').read()

extras_require = {
    'invenio3.2': [
        'invenio[base,metadata,files,postgresql,elasticsearch7]>=3.2.0,<3.3.0',
    ],
    'invenio3.3': [
        'invenio[base,metadata,files,postgresql,elasticsearch7]>=3.3.0,<3.4.0',
    ],
    'devel': [
        'invenio[base,postgresql,elasticsearch7]',
    ],
}

packages = find_packages()

setup(
    name='invenio-integration-tests',
    version='0.0.1',
    description='invenio integration tests',
    long_description=readme,
    keywords='Invenio oarepo',
    license='MIT',
    author='Tomas HLava @ CESNET',
    author_email='hlava@cesnet.cz',
    url='https://github.com/oarepo/invenio-integration-tests',
    packages=packages,
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    entry_points={},
    extras_require=extras_require,
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Development Status :: 3 - Alpha',
    ],
)
