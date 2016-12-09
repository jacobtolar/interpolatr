#!/usr/bin/env python

from setuptools import setup

# see https://github.com/pypa/pypi-legacy/issues/148
try:
    import pypandoc
    readme = pypandoc.convert('README.md', 'rst')
except ImportError:
    readme = open('README.md').read()


packages = [
    'interpolatr'
]

requirements = [
    'click>=6.0',
    'Jinja2>=2.8',
    'PyYAML>=3.12'
]

extras_require = {
    ":python_version < '3.0'": ['chainmap>=1.0.2']
}

with open('interpolatr/__init__.py', 'r') as f:
    for line in f:
        if line.startswith('__version__'):
            parts = line.split('=')
            version = parts[1].strip().strip("'")
            break

if not version:
    raise RuntimeError('Cannot find version information')

setup(
    name='interpolatr',
    version=version,
    description='Interpolation tool',
    long_description=readme,
    author='Jacob Tolar',
    author_email='development@sheckel.net',
    url='http://github.com/jacobtolar/interpolatr',
    packages=['interpolatr'],
    package_data={'': ['LICENSE']},
    include_package_data=True,
    install_requires=requirements,
    license='Apache 2.0',
    zip_safe=False,
    classifiers=(
            'Programming Language :: Python',
            'Programming Language :: Python :: 2.7'
    ),
    scripts=['scripts/interpolatr'],
    extras_require=extras_require
)
