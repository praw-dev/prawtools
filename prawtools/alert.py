"""prawtools.alert provides the reddit_alert command that will alert you when
chosen keywords appear in reddit comments."""

from __future__ import print_function, unicode_literals

import re
import praw
import sys
from update_checker import update_check
from . import __version__
from .helpers import arg_parser


def quick_url(comment):
    """Return the URL for the comment without fetching its submission."""
    def to_id(fullname):
        return fullname.split('_', 1)[1]
    return ('http://www.reddit.com/r/{0}/comments/{1}/_/{2}?context=3'
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
                            'alert. Requires the alert script to login.'))
    options, args = parser.parse_args()
    if not args:
        parser.error('At least one KEYWORD must be provided.')

    # Create the reddit session, and login if necessary
    session = praw.Reddit('reddit_alert (prawtools {0})'.format(__version__),
                          site_name=options.site, disable_update_check=True)
    if options.message:
        session.login(options.user, options.pswd)
        msg_to = session.get_redditor(options.message)

    # Check for updates
    if not options.disable_update_check:
        update_check('prawtools', __version__)

    # Build regex
    args = [x.lower() for x in args]
    reg_prefix = r'(?:^|[^a-z])'  # Any character (or start) can precede
    reg_suffix = r'(?:$|[^a-z])'  # Any character (or end) can follow
    regex = re.compile(r'{0}({1}){2}'.format(reg_prefix, '|'.join(args),
                                             reg_suffix), re.IGNORECASE)

    # Determine subreddit or multireddit
    if options.subreddit:
        subreddit = '+'.join(sorted(options.subreddit))
    else:
        subreddit = 'all'

    print('Alerting on:')
    for item in sorted(args):
        print(' * {0}'.format(item))
    print ('using the comment stream: http://www.reddit.com/r/{0}/comments'
           .format(subreddit))

    # Build ignore set
    if options.ignore_user:
        ignore_users = set(x.lower() for x in options.ignore_user)
    else:
        ignore_users = set()

    try:
        for comment in praw.helpers.comment_stream(session, subreddit,
                                                   verbosity=options.verbose):
            if comment.author and comment.author.name.lower() in ignore_users:
                continue
            match = regex.search(comment.body)
            if match:
                keyword = match.group(1).lower()
                url = quick_url(comment)
                print('{0}: {1}'.format(keyword, url))
                if options.message:
                    msg_to.send_message(
                        'Reddit Alert: {0}'.format(keyword),
                        '{0}\n\nby /u/{1}\n\n---\n\n{2}'.format(
                            url, comment.author, comment.body))
    except KeyboardInterrupt:
        sys.stderr.write('\n')
        print('Goodbye!\n')
