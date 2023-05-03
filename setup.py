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
        'invenio[base,metadata,files,postgresql,elasticsearch7,tests]>=3.2.0,<3.3.0'
    ],
    'invenio3.3': [
        'invenio[base,metadata,files,postgresql,elasticsearch7]>=3.3.0,<3.4.0',
        'invenio-accounts==1.4.2',
        'invenio-base==1.2.13',
        'requests',
        's3-client-lib',
        'flask-oauthlib',
        'invenio-oauthclient==1.4.0',
        'invenio-oauth2server==1.3.1',
        'pytest-cov==2.10.1',
        'coverage==4.5.4',
        'pillow>=8.3.2'
    ],
    'invenio3.3test': [
        'invenio[base,metadata,files,postgresql,elasticsearch7,tests]>=3.3.0,<3.4.0',
        'invenio-accounts==1.4.2',
        'invenio-base==1.2.13',
        'requests',
        's3-client-lib',
        'flask-oauthlib',
        'invenio-oauthclient==1.4.0',
        'invenio-oauth2server==1.3.1',
        'pytest-cov==2.10.1',
        'coverage==4.5.4',
        'pillow>=8.3.2'
    ],
    'devel': [
        'invenio[base,metadata,files,postgresql,elasticsearch7]',
    ],
    'devel_test': [
        'invenio[base,metadata,files,postgresql,elasticsearch7,tests]',
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
