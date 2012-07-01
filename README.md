# Introduction

subreddit_stats.py is a tool to provide basic statistics on a subreddit.
To see the what sort of output subreddit stats generates check out
[/r/subreddit_stats](http://www.reddit.com/r/subreddit_stats).

# Installation

## Ubuntu/debian installation

    sudo apt-get install python-setuptools
    sudo easy_install pip
    sudo pip install subreddit_stats

## Mac OS X installation (only tested with Lion)

    sudo easy_install pip
    sudo pip install subreddit_stats

# Examples of how to run subreddit_stats

0. Generate stats for subreddit __foo__ for the last 30 days with extra
verbose output. Post results to subreddit __bar__ as user __user__.

    subreddit_stats -d30 -vv -R bar -u user foo

0. Generate stats for subreddit __blah__ for the top posts of the year. Post the
results to the same subreddit as user __resu__.

    subreddit_stats --top year -u resu blah
