"""Test prawtools."""
import unittest

from betamax import Betamax


class IntegrationTest(unittest.TestCase):
    """Base class for prawtools integration tests."""

    def setUp(self, http):
        """Setup runs before all test cases."""
        self.recorder = Betamax(http)

        # Disable response compression in order to see the response bodies in
        # the betamax cassettes.
        http.headers['Accept-Encoding'] = 'identity'
