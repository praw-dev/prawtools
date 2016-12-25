"""prawtools setup.py."""

import re
from codecs import open
from os import path
from setuptools import setup


PACKAGE_NAME = 'prawtools'
HERE = path.abspath(path.dirname(__file__))
with open(path.join(HERE, 'README.md'), encoding='utf-8') as fp:
    README = fp.read()
with open(path.join(HERE, PACKAGE_NAME, '__init__.py'),
          encoding='utf-8') as fp:
    VERSION = re.search("__version__ = '([^']+)'", fp.read()).group(1)


setup(name=PACKAGE_NAME,
      author='Bryce Boe',
      author_email='bbzbryce@gmail.com',
      classifiers=['Environment :: Console',
                   'Intended Audience :: Developers',
                   'License :: OSI Approved :: BSD License',
                   'Natural Language :: English',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python :: 2.7',
                   'Programming Language :: Python :: 3',
                   'Programming Language :: Python :: 3.3',
                   'Programming Language :: Python :: 3.4',
                   'Programming Language :: Python :: 3.5',
                   'Topic :: Utilities'],
      description='A collection of utilities that utilize the reddit API.',
      entry_points={
          'console_scripts': ['modutils = prawtools.mod:main',
                              'reddit_alert = prawtools.alert:main',
                              'subreddit_stats = prawtools.stats:main']},
      install_requires=['praw >=4.0.0, <5'],
      keywords='reddit mod moderator subreddit statistics tools',
      license='Simplified BSD License',
      long_description=README,
      packages=[PACKAGE_NAME],
      test_suite='tests',
      tests_require=['betamax >=0.7.1, <0.8',
                     'betamax-serializers >=0.2.0, <0.3',
                     'mock ==1.0.1'],
      url='https://github.com/praw-dev/prawtools',
      version=VERSION)
