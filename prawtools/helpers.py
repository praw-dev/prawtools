from optparse import OptionGroup, OptionParser
from . import __version__


def arg_parser(*args, **kwargs):
    msg = {
        'site': 'The site to connect to defined in your praw.ini file.',
        'user': ('The user to login as. If not specified the user (if any) '
                 'from the site config will be used, otherwise you will be '
                 'prompted for a username.'),
        'pswd': ('The password to use for login. Can only be used in '
                 'combination with "--user". See help for "--user".')}

    kwargs['version'] = 'BBoe\'s PRAWtools {0}'.format(__version__)
    parser = OptionParser(*args, **kwargs)
    parser.add_option('-v', '--verbose', action='count', default=0,
                      help='Increase the verbosity by 1 each time')

    group = OptionGroup(parser, 'Site/Authentication options')
    group.add_option('-S', '--site', help=msg['site'])
    group.add_option('-u', '--user', help=msg['user'])
    group.add_option('-p', '--pswd', help=msg['pswd'])
    parser.add_option_group(group)

    return parser
