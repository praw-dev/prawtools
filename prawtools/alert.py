"""prawtools.alert provides the reddit_alert command.

This command will alert you when chosen keywords appear in reddit comments.

"""
from __future__ import print_function

import re
import sys

import praw

from .helpers import AGENT, arg_parser, check_for_updates


def quick_url(comment):
    """Return the URL for the comment without fetching its submission."""
    def to_id(fullname):
        return fullname.split('_', 1)[1]
    return ('http://www.reddit.com/r/{}/comments/{}/_/{}?context=3'
            .format(comment.subreddit.display_name, to_id(comment.link_id),
                    comment.id))


def main():
    """Provide the entry point into the reddit_alert program."""
    usage = 'Usage: %prog [options] KEYWORD...'
    parser = arg_parser(usage=usage)
    parser.add_option('-s', '--subreddit', action='append',
                      help=('When at least one `-s` option is provided '
                            '(multiple can be) only alert for comments in the '
                            'indicated subreddit(s).'))
    parser.add_option('-I', '--ignore-user', action='append', metavar='USER',
                      help=('Ignore comments from the provided user. Can be '
                            'supplied multiple times.'))
    parser.add_option('-m', '--message', metavar='USER',
                      help=('When set, send a reddit message to USER with the '
                            'alert.'))
    options, args = parser.parse_args()
    if not args:
        parser.error('At least one KEYWORD must be provided.')

    session = praw.Reddit(options.site, check_for_updates=False,
                          user_agent=AGENT)

    if options.message:
        msg_to = session.redditor(options.message)

    check_for_updates(options)

    # Build regex
    args = [x.lower() for x in args]
    reg_prefix = r'(?:^|[^a-z])'  # Any character (or start) can precede
    reg_suffix = r'(?:$|[^a-z])'  # Any character (or end) can follow
    regex = re.compile(r'{}({}){}'.format(reg_prefix, '|'.join(args),
                                          reg_suffix), re.IGNORECASE)

    # Determine subreddit or multireddit
    if options.subreddit:
        subreddit = '+'.join(sorted(options.subreddit))
    else:
        subreddit = 'all'

    print('Alerting on:')
    for item in sorted(args):
        print(' * {}'.format(item))
    print('using the comment stream: https://www.reddit.com/r/{}/comments'
          .format(subreddit))

    # Build ignore set
    if options.ignore_user:
        ignore_users = set(x.lower() for x in options.ignore_user)
    else:
        ignore_users = set()

    try:
        for comment in session.subreddit(subreddit).stream.comments():
            if comment.author and comment.author.name.lower() in ignore_users:
                continue
            match = regex.search(comment.body)
            if match:
                keyword = match.group(1).lower()
                url = quick_url(comment)
                print('{}: {}'.format(keyword, url))
                if options.message:
                    msg_to.message(
                        'Reddit Alert: {}'.format(keyword),
                        '{}\n\nby /u/{}\n\n---\n\n{}'.format(
                            url, comment.author, comment.body))
    except KeyboardInterrupt:
        sys.stderr.write('\n')
        print('Goodbye!\n')
