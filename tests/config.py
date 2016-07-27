"""Constants for the prawtools test suite."""

import os
from base64 import b64encode

from betamax import Betamax
from betamax_serializers import pretty_json


def b64_string(input_string):
    """Return a base64 encoded string (not bytes) from input_string."""
    return b64encode(input_string.encode('utf-8')).decode('utf-8')


def env_default(key):
    """Return environment variable or placeholder string.

    Set environment variable to placeholder if it doesn't exist.
    """
    test_environ = 'prawtest_{}'.format(key)
    test_value = os.environ.get(test_environ, 'placeholder_{}'.format(key))
    return os.environ.setdefault('praw_{}'.format(key), test_value)


os.environ['praw_check_for_updates'] = 'False'


placeholders = {x: env_default(x) for x in
                'client_id client_secret password username'.split()}
placeholders['basic_auth'] = b64_string(
    '{}:{}'.format(placeholders['client_id'], placeholders['client_secret']))


Betamax.register_serializer(pretty_json.PrettyJSONSerializer)
with Betamax.configure() as config:
    if os.getenv('TRAVIS'):
        config.default_cassette_options['record_mode'] = 'none'
    config.cassette_library_dir = 'tests/cassettes'
    config.default_cassette_options['serialize_with'] = 'prettyjson'
    config.default_cassette_options['match_requests_on'].append('body')
    for key, value in placeholders.items():
        config.define_cassette_placeholder('<{}>'.format(key.upper()), value)
