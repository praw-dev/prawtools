import os
import re
from setuptools import setup

PACKAGE_NAME = 'prawtools'


HERE = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(HERE, 'README.md')) as fp:
    README = fp.read()
with open(os.path.join(HERE, PACKAGE_NAME, '__init__.py')) as fp:
    VERSION = re.search("__version__ = '([^']+)'", fp.read()).group(1)


setup(name=PACKAGE_NAME,
      version=VERSION,
      author='Bryce Boe',
      author_email='bbzbryce@gmail.com',
      license='Simplified BSD License',
      url='https://github.com/praw-dev/prawtools',
      description=('A collection of utilities that utilize the reddit API.'),
      long_description=README,
      keywords='reddit mod moderator subreddit statistics tools',
      classifiers=['Environment :: Console',
                   'Intended Audience :: Developers',
                   'License :: OSI Approved :: BSD License',
                   'Natural Language :: English',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python :: 2.6',
                   'Programming Language :: Python :: 2.7',
                   'Programming Language :: Python :: 3',
                   'Programming Language :: Python :: 3.1',
                   'Programming Language :: Python :: 3.2',
                   'Programming Language :: Python :: 3.3',
                   'Topic :: Utilities'],
      install_requires=['praw>=2.1.2', 'update_checker>=0.7'],
      packages=[PACKAGE_NAME],
      entry_points={'console_scripts':
                        ['modutils = prawtools.mod:main',
                         'reddit_alert = prawtools.alert:main',
                         'subreddit_stats = prawtools.stats:main']},
      test_suite='tests')
