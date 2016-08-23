"""prawtools.mod provides the modutils command.

This command allows you to view and change some subreddit options.

"""
from __future__ import print_function
import json
import re
import sys
from collections import Counter
from optparse import OptionGroup

from praw import Reddit
from six.moves import input

from .helpers import AGENT, arg_parser, check_for_updates


class ModUtils(object):
    """Class that provides all the modutils functionality."""

    def __init__(self, subreddit, site=None, verbose=None):
        """Initialize the ModUtils class by passing in config options."""
        self.reddit = Reddit(site, check_for_updates=False, user_agent=AGENT)
        self.sub = self.reddit.subreddit(subreddit)
        self.verbose = verbose
        self._current_flair = None

    def add_users(self, category):
        """Add users to 'banned', 'contributor', or 'moderator'."""
        mapping = {'banned': 'ban', 'contributor': 'make_contributor',
                   'moderator': 'make_moderator'}

        if category not in mapping:
            print('{!r} is not a valid option for --add'.format(category))
            return
        func = getattr(self.sub, mapping[category])
        print('Enter user names (any separation should suffice):')
        data = sys.stdin.read().strip()
        for name in re.split('[^A-Za-z0-9_]+', data):
            func(name)
            print('Added {!r} to {}'.format(name, category))

    def clear_empty(self):
        """Remove flair that is not visible or has been set to empty."""
        for flair in self.current_flair():
            if not flair['flair_text'] and not flair['flair_css_class']:
                print(self.reddit.flair.update(flair['user']))
                print('Removed flair for {0}'.format(flair['user']))

    def current_flair(self):
        """Generate the flair, by user, for the subreddit."""
        if self._current_flair is None:
            self._current_flair = []
            if self.verbose:
                print('Fetching flair list for {}'.format(self.sub))
            for flair in self.sub.flair:
                self._current_flair.append(flair)
                yield flair
        else:
            for item in self._current_flair:
                yield item

    def flair_template_sync(self, editable, limit,  # pylint: disable=R0912
                            static, sort, use_css, use_text):
        """Synchronize templates with flair that already exists on the site.

        :param editable: Indicates that all the options should be editable.
        :param limit: The minimum number of users that must share the flair
            before it is added as a template.
        :param static: A list of flair templates that will always be added.
        :param sort: The order to sort the flair templates.
        :param use_css: Include css in the templates.
        :param use_text: Include text in the templates.

        """
        # Parameter verification
        if not use_text and not use_css:
            raise Exception('At least one of use_text or use_css must be True')
        sorts = ('alpha', 'size')
        if sort not in sorts:
            raise Exception('Sort must be one of: {}'.format(', '.join(sorts)))

        # Build current flair list along with static values
        counter = {}
        if static:
            for key in static:
                if use_css and use_text:
                    parts = tuple(x.strip() for x in key.split(','))
                    if len(parts) != 2:
                        raise Exception('--static argument {!r} must have two '
                                        'parts (comma separated) when using '
                                        'both text and css.'.format(parts))
                    key = parts
                counter[key] = limit
        if self.verbose:
            sys.stdout.write('Retrieving current flair\n')
            sys.stdout.flush()
        for flair in self.current_flair():
            if self.verbose:
                sys.stdout.write('.')
                sys.stdout.flush()
            if use_text and use_css:
                key = (flair['flair_text'], flair['flair_css_class'])
            elif use_text:
                key = flair['flair_text']
            else:
                key = flair['flair_css_class']
            if key in counter:
                counter[key] += 1
            else:
                counter[key] = 1
        if self.verbose:
            print()

        # Sort flair list items according to the specified sort
        if sort == 'alpha':
            items = sorted(counter.items())
        else:
            items = sorted(counter.items(), key=lambda x: x[1], reverse=True)

        # Clear current templates and store flair according to the sort
        if self.verbose:
            print('Clearing current flair templates')
        self.sub.flair.templates.clear()
        for key, count in items:
            if not key or count < limit:
                print('a')
                continue
            if use_text and use_css:
                text, css = key
            elif use_text:
                text, css = key, ''
            else:
                text, css = '', key
            if self.verbose:
                print('Adding template: text: {!r} css: {!r}'
                      .format(text, css))
            self.sub.flair.templates.add(text, css, editable)

    def message(self, category, subject, msg_file):
        """Send message to all users in `category`."""
        users = getattr(self.sub, category)
        if not users:
            print('There are no {} users on {}.'.format(category, self.sub))
            return

        if msg_file:
            try:
                msg = open(msg_file).read()
            except IOError as error:
                print(str(error))
                return
        else:
            print('Enter message:')
            msg = sys.stdin.read()

        print('You are about to send the following message to the users {}:'
              .format(', '.join([str(x) for x in users])))
        print('---BEGIN MESSAGE---\n{}\n---END MESSAGE---'.format(msg))
        if input('Are you sure? yes/[no]: ').lower() not in ['y', 'yes']:
            print('Message sending aborted.')
            return
        for user in users:
            user.send_message(subject, msg)
            print('Sent to: {}'.format(user))

    def output_current_flair(self, as_json=False):
        """Display the current flair for all users in the subreddit."""
        flair_list = sorted(self.current_flair(), key=lambda x: x['user'].name)
        if as_json:
            print(json.dumps(flair_list, sort_keys=True, indent=4))
            return

        for flair in flair_list:
            print(flair['user'])
            print('  Text: {}\n   CSS: {}'.format(flair['flair_text'],
                                                  flair['flair_css_class']))

    def output_flair_stats(self):
        """Display statistics (number of users) for each unique flair item."""
        css_counter = Counter()
        text_counter = Counter()
        for flair in self.current_flair():
            if flair['flair_css_class']:
                css_counter[flair['flair_css_class']] += 1
            if flair['flair_text']:
                text_counter[flair['flair_text']] += 1

        print('Flair CSS Statistics')
        for flair, count in sorted(css_counter.items(),
                                   key=lambda x: (x[1], x[0])):
            print('{0:3} {1}'.format(count, flair))

        print('Flair Text Statistics')
        for flair, count in sorted(text_counter.items(),
                                   key=lambda x: (x[1], x[0]), reverse=True):
            print('{0:3} {1}'.format(count, flair))

    def output_list(self, category):
        """Display the list of users in `category`."""
        print('{} users:'.format(category))
        for user in getattr(self.sub, category):
            print('  {}'.format(user))


def main():
    """Provide the entry point in the the modutils command."""
    mod_choices = ('banned', 'contributor', 'moderator')
    mod_choices_dsp = ', '.join(['`{}`'.format(x) for x in mod_choices])
    msg = {
        'add': ('Add users to one of the following categories: {}'
                .format(mod_choices_dsp)),
        'clear': 'Remove users who have no flair set.',
        'css': 'Ignore the CSS field when synchronizing flair.',
        'edit': 'When adding flair templates, mark them as editable.',
        'file': 'The file containing contents for --message',
        'flair': 'List flair for the subreddit.',
        'flair_stats': 'Display the number of users with each flair.',
        'json': 'Output the results as json. Applies to --flair',
        'limit': ('The minimum number of users that must have the specified '
                  'flair in order to add as a template. default: %default'),
        'list': ('List the users in one of the following categories: '
                 '{}. May be specified more than once.'
                 .format(mod_choices_dsp)),
        'msg': ('Send message to users of one of the following categories: '
                '{}. Message subject provided via --subject, content provided '
                'via --file or STDIN.').format(mod_choices_dsp),
        'sort': ('The order to add flair templates. Available options are '
                 '`alpha` to add alphabetically, and `size` to first add '
                 'flair that is shared by the most number of users. '
                 'default: %default'),
        'static': ('Add this template when syncing flair templates. When '
                   'syncing text and css use a comma to separate the two.'),
        'subject': 'The subject of the message to send for --message.',
        'sync': 'Synchronize flair templates with current user flair.',
        'text': 'Ignore the text field when synchronizing flair.'}

    usage = 'Usage: %prog [options] SUBREDDIT'
    parser = arg_parser(usage=usage)
    parser.add_option('-a', '--add', help=msg['add'])
    parser.add_option('-l', '--list', action='append', help=msg['list'],
                      choices=mod_choices, metavar='CATEGORY', default=[])
    parser.add_option('-c', '--clear-empty', action='store_true',
                      help=msg['clear'])
    parser.add_option('-F', '--file', help=msg['file'])
    parser.add_option('-f', '--flair', action='store_true', help=msg['flair'])
    parser.add_option('', '--flair-stats', action='store_true',
                      help=msg['flair_stats'])
    parser.add_option('-m', '--message', choices=mod_choices, help=msg['msg'])
    parser.add_option('', '--subject', help=msg['subject'])

    group = OptionGroup(parser, 'Format options')
    group.add_option('-j', '--json', action='store_true', help=msg['json'])
    parser.add_option_group(group)

    group = OptionGroup(parser, 'Sync options')
    group.add_option('', '--sync', action='store_true', help=msg['sync'])
    group.add_option('-s', '--static', action='append', help=msg['static'])
    group.add_option('', '--editable', action='store_true', help=msg['edit'])
    group.add_option('', '--ignore-css', action='store_true',
                     default=False, help=msg['css'])
    group.add_option('', '--ignore-text', action='store_true',
                     default=False, help=msg['text'])
    group.add_option('', '--limit', type='int', help=msg['limit'], default=2)
    group.add_option('', '--sort', action='store', choices=('alpha', 'size'),
                     default='alpha', help=msg['sort'])
    parser.add_option_group(group)

    options, args = parser.parse_args()
    if len(args) == 0:
        parser.error('Must provide subreddit name.')
    if options.message and not options.subject:
        parser.error('Must provide --subject when providing --message.')
    subreddit = args[0]

    check_for_updates(options)

    modutils = ModUtils(subreddit, options.site, options.verbose)

    if options.add:
        modutils.add_users(options.add)
    if options.clear_empty:
        modutils.clear_empty()
    for category in options.list:
        modutils.output_list(category)
    if options.flair:
        modutils.output_current_flair(as_json=options.json)
    if options.flair_stats:
        modutils.output_flair_stats()
    if options.sync:
        modutils.flair_template_sync(editable=options.editable,
                                     limit=options.limit,
                                     static=options.static, sort=options.sort,
                                     use_css=not options.ignore_css,
                                     use_text=not options.ignore_text)
    if options.message:
        modutils.message(options.message, options.subject, options.file)
