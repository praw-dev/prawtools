# BBOE's PRAWtools

PRAWtools is a collection of tools that utilize reddit's API through the Python
Reddit API Wrapper (PRAW). PRAWtools is currently made up of two utillities:

* modutils
* subreddit_stats

## PRAWtools Installation

### Ubuntu/debian installation

    sudo apt-get install python-setuptools
    sudo easy_install pip
    sudo pip install prawtools

### Arch Linux installation
    sudo pacman -S python-pip
    sudo easy_install pip
    sudo pip install prawtools

### Mac OS X installation (only tested with Lion)

    sudo easy_install pip
    sudo pip install prawtools


## modutils

modutils is a tool to assist Reddit community moderators in moderating
their community. At present, it is mostly useful for automatically building
flair templates from existing user flair, however, it can also be used to
quickly list banned users, contributors, and moderators.

### modutils examples

Note: all examples require you to be a moderator for the subreddit

0. List banned users for subreddit __foo__

        modutils -l banned foo

0. Get current flair for subreddit __bar__

        modutils -f bar

0. Synchronize flair templates with existing flair for subreddit __baz__,
building non-editable templates for any flair whose flair-text is common among
at least 2 users.

        modutils --sync --ignore-css --limit=2 baz

0. Send a message to approved submitters of subreddit __blah__. You will be
prompted for the message, and asked to verify prior to sending the messages.

        modutils --message contributors --subject "The message subject" blah


## subreddit_stats

subreddit_stats is a tool to provide basic statistics on a subreddit.
To see the what sort of output subreddit stats generates check out
[/r/subreddit_stats](http://www.reddit.com/r/subreddit_stats).


### subreddit_stats examples

0. Generate stats for subreddit __foo__ for the last 30 days with extra
verbose output. Post results to subreddit __bar__ as user __user__.

        subreddit_stats -d30 -vv -R bar -u user foo

0. Generate stats for subreddit __blah__ for the top posts of the year. Post
the results to the same subreddit as user __resu__.

        subreddit_stats --top year -u resu blah

0. To see other possible options

        subreddit_stats --help
