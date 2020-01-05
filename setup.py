"""prawtools setup.py."""

import re
from codecs import open
from os import path
from setuptools import setup


PACKAGE_NAME = "prawtools"
HERE = path.abspath(path.dirname(__file__))
with open(path.join(HERE, "README.md"), encoding="utf-8") as fp:
    README = fp.read()
with open(path.join(HERE, PACKAGE_NAME, "__init__.py"), encoding="utf-8") as fp:
    VERSION = re.search('__version__ = "([^"]+)', fp.read()).group(1)


extras = {
    "ci": ["coveralls"],
    "lint": ["black", "flake8", "pydocstyle"],
    "test": [
        "betamax >=0.7.1, <0.8",
        "betamax-serializers >=0.2.0, <0.3",
        "mock ==1.0.1",
        "pytest",
    ],
}
required = ["praw >=4.0.0, <7", "six >=1, <2"]


setup(
    name=PACKAGE_NAME,
    author="Bryce Boe",
    author_email="bbzbryce@gmail.com",
    classifiers=[
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Topic :: Utilities",
    ],
    description="A collection of utilities that utilize the reddit API.",
    entry_points={
        "console_scripts": [
            "modutils = prawtools.mod:main",
            "reddit_alert = prawtools.alert:main",
            "subreddit_stats = prawtools.stats:main",
        ]
    },
    extras_require=extras,
    install_requires=required,
    keywords="reddit mod moderator subreddit statistics tools",
    license="Simplified BSD License",
    long_description=README,
    packages=[PACKAGE_NAME],
    url="https://github.com/praw-dev/prawtools",
    version=VERSION,
)
