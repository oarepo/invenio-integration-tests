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

install_requires = [
    # Invenio core modules
    'invenio-app>=1.3.4,<1.4.0',
    'invenio-base>=1.2.11,<1.3.0',
    'invenio-cache>=1.1.1,<1.2.0',
    'invenio-celery>=1.2.4,<1.3.0',
    'invenio-config>=1.0.3,<1.1.0',
    'invenio-i18n>=1.3.1,<1.4.0',
    'invenio-db[postgresql,mysql,versioning]>=1.0.14,<1.1.0',
    # Invenio base bundle
    'invenio-admin>=1.3.2,<1.4.0',
    'invenio-assets>=1.2.7,<1.3.0',
    'invenio-formatter>=1.1.3,<1.2.0',
    'invenio-logging[sentry-sdk]>=1.3.2,<1.4.0',
    'invenio-mail>=1.0.2,<1.1.0',
    'invenio-rest>=1.2.8,<1.3.0',
    'invenio-theme>=1.3.23,<1.4.0',
    # Invenio auth bundle
    'invenio-access>=1.4.4,<1.5.0',
    'invenio-accounts>=2.0.0,<2.1.0',
    'invenio-oauth2server>=1.3.5,<1.4.0',
    'invenio-oauthclient>=2.0.0.dev0,<2.1.0',
    'invenio-userprofiles>=2.0.0,<2.1.0',
    # Invenio metdata bundle
    'invenio-indexer>=1.2.7,<1.3.0',
    'invenio-jsonschemas>=1.1.4,<1.2.0',
    'invenio-oaiserver>=1.4.2,<1.5.0',
    'invenio-pidstore>=1.2.3,<1.3.0',
    'invenio-records-rest>=1.9.0,<1.10.0',
    'invenio-records-ui>=1.2.0,<1.3.0',
    'invenio-records>=1.7.3,<1.8.0',
    'invenio-search-ui>=2.1.1,<2.2.0',
    # Invenio files bundle
    'invenio-files-rest>=1.3.3,<1.4.0',
    'invenio-previewer>=1.3.6,<1.4.0',
    'invenio-records-files>=1.2.1,<1.3.0',
    # Invenio-App-RDM
#    'invenio-rdm-records>=0.35.16,<0.36.0',
    'CairoSVG>=2.5.2,<3.0.0',
    # Werkzeug - due to https://github.com/pallets/werkzeug/issues/2397
    'Werkzeug>=1.0,!=2.1.0,!=2.1.1',
]

extras_require = {
    'tests': [
        'pytest-black>=0.3.0,<0.3.10',
        'pytest-invenio~=1.4.7',
        'Sphinx>=4.2.0',
    ],
    'elasticsearch7': [
        'invenio-search[elasticsearch7]>=1.4.2,<1.5.0',
    ],
    's3': [
        'invenio-s3~=1.0.5',
    ]
}

setup_requires = [
    'pytest-runner>=3.0.0,<5',
]

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
    install_requires=install_requires,
    setup_requires=setup_requires,
    extras_require=extras_require,
    tests_require=extras_require['tests'],
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Development Status :: 3 - Alpha',
    ],
)
