import os
import re
from setuptools import setup

HERE = os.path.abspath(os.path.dirname(__file__))
MODULE_FILE = os.path.join(HERE, 'subreddit_stats.py')
README = open(os.path.join(HERE, 'README.md'))
VERSION = re.search("__version__ = '([^']+)'",
                    open(MODULE_FILE).read()).group(1)

NAME = 'subreddit_stats'


setup(name=NAME,
      version=VERSION,
      author='Bryce Boe',
      author_email='bbzbryce@gmail.com',
      url='https://github.com/praw-dev/subreddit_stats',
      description=('A tool to calculate various submission and comment '
                   'statistics on reddit communities.'),
      long_description=README,
      keywords = 'reddit subreddit statistics',
      classifiers=['Programming Language :: Python'],
      install_requires=['praw'],
      py_modules=[NAME],
      entry_points = {'console_scripts': ['{0} = {0}:main'.format(NAME)]})
