"""prawtools.helpers provides functions useful in other prawtools modules."""
from optparse import OptionGroup, OptionParser

from update_checker import update_check

from . import __version__


AGENT = 'prawtools/{}'.format(__version__)


def arg_parser(*args, **kwargs):
    """Return a parser with common options used in the prawtools commands."""
    msg = {
        'site': 'The site to connect to defined in your praw.ini file.',
        'update': 'Prevent the checking for prawtools package updates.'}

    kwargs['version'] = 'BBoe\'s PRAWtools {}'.format(__version__)
    parser = OptionParser(*args, **kwargs)
    parser.add_option('-v', '--verbose', action='count', default=0,
                      help='Increase the verbosity by 1 each time')
    parser.add_option('-U', '--disable-update-check', action='store_true',
                      help=msg['update'])

    group = OptionGroup(parser, 'Site/Authentication options')
    group.add_option('-S', '--site', help=msg['site'])
    parser.add_option_group(group)

    return parser


def check_for_updates(options):
    """Check for package updates."""
    if not options.disable_update_check:  # Check for updates
        update_check('prawtools', __version__)
