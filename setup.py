#!/usr/bin/env python
from setuptools import setup, find_packages
from sass_processor import __version__

with open('README.md', 'r') as fh:
    long_description = fh.read()

CLASSIFIERS = [
    'Development Status :: 5 - Production/Stable',
    'Environment :: Web Environment',
    'Framework :: Django',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: MIT License',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    'Programming Language :: Python :: 3.5',
    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: 3.7',
    'Programming Language :: Python :: 3.8',
    'Framework :: Django :: 1.11',
    'Framework :: Django :: 2.0',
    'Framework :: Django :: 2.1',
    'Framework :: Django :: 2.2',
    'Framework :: Django :: 3.0',
    'Framework :: Django :: 3.1',
]

setup(
    name='django-sass-processor',
    version=__version__,
    description='SASS processor to compile SCSS files into *.css, while rendering, or offline.',
    author='Jacob Rief',
    author_email='jacob.rief@gmail.com',
    url='https://github.com/jrief/django-sass-processor',
    install_requires=[],
    extras_require={
        'management-command': [
            'django-compressor>=2.4',
        ],
        'dev': [
            'libsass>=0.13',
        ],
    },
    license='MIT',
    keywords=['django', 'sass'],
    platforms=['OS Independent'],
    classifiers=CLASSIFIERS,
    long_description=long_description,
    long_description_content_type='text/markdown',
    include_package_data=True,
    packages=find_packages(exclude=['tests']),
    zip_safe=False,
)
