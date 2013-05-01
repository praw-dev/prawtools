from __future__ import print_function, unicode_literals

import re
import praw
from .helpers import arg_parser


def quick_url(comment):
    """Provide the URL for the comment without fetching its submission."""
    def to_id(fullname):
        return fullname.split('_', 1)[1]
    return ('http://www.reddit.com/r/{0}/comments/{1}/_/{2}?context=3'
            .format(comment.subreddit.display_name, to_id(comment.link_id),
                    comment.id))


def main():
    usage = 'Usage: %prog [options] KEYWORD...'
    parser = arg_parser(usage=usage)
    parser.add_option('-s', '--subreddit', action='append',
                      help=('When at least one `-s` option is provided '
                            '(multiple can be) only alert for comments in the '
                            'indicated subreddit(s).'))
    options, args = parser.parse_args()
    if not args:
        parser.error('At least one KEYWORD must be provided.')

    # Build regex
    reg_prefix = r'(?:^|[^a-z])'  # Any character (or start) can precede
    reg_suffix = r'(?:$|[^a-z])'  # Any character (or end) can follow
    regex = re.compile(r'{0}({1}){2}'.format(reg_prefix, '|'.join(args),
                                             reg_suffix), re.IGNORECASE)

    # Determine subreddit or multireddit
    if options.subreddit:
        subreddit = '+'.join(sorted(options.subreddit))
    else:
        subreddit = 'all'

    print('Searching for:')
    for item in sorted(args):
        print(' * {0}'.format(item))
    print ('using the comment stream: http://www.reddit.com/r/{0}/comments'
           .format(subreddit))

    r = praw.Reddit('Reddit Alerts by /u/bboe')
    for comment in praw.helpers.comment_stream(r, subreddit, options.verbose):
        match = regex.search(comment.body)
        if match:
            print('{0}: {1}'.format(match.group(1).lower(),
                                    quick_url(comment)))
