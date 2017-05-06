#!/usr/bin/env python

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

long_discription = readme + '\n\n' + history

install_requires = [
    'attrs>=16.2.0',
    'PyLD>=0.7.1',
]

tests_require = [
    'tox>=2.3.1',
    'coverage>=4.1',
    'flake8>=2.6.0',
    'pytest>=3.0.1',
    'pytest-cov',
    'pytest-mock',
]

dev_require = [
    'ipdb',
    'ipython',
]

docs_require = [
    'Sphinx>=1.4.4',
    'sphinx-autobuild',
    'sphinxcontrib-napoleon>=0.4.4',
    'sphinx_rtd_theme',
]

setup(
    name='coalaip',
    version='0.0.3',
    description="Python reference implementation for COALA IP",
    long_description=long_discription,
    author="BigchainDB",
    author_email='dev@bigchaindb.com',
    url='https://github.com/bigchaindb/pycoalaip',
    packages=find_packages(exclude=['tests*']),
    include_package_data=True,
    install_requires=install_requires,
    tests_require=tests_require,
    extras_require={
        'test': tests_require,
        'dev': dev_require + tests_require + docs_require,
        'docs': docs_require,
    },
    test_suite='tests',
    license="Apache Software License 2.0",
    keywords='coalaip',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
)
