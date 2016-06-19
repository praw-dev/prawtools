"""Test subreddit_stats."""
import mock
from prawtools.stats import SubRedditStats

from . import IntegrationTest


class StatsTest(IntegrationTest):
    def setUp(self):
        """Setup runs before all test cases."""
        self.srs = SubRedditStats('redditdev', None, None, None)
        super(StatsTest, self).setUp(self.srs.reddit._core._requestor._http)

    def test_recent(self):
        with self.recorder.use_cassette('StatsTest.test_recent'):
            self.assertTrue(
                self.srs.fetch_recent_submissions(
                    max_duration=7, after=None, exclude_self=False,
                    exclude_link=False))
            self.assertTrue(len(self.srs.submissions) > 1)
            prev = 0
            for submission in self.srs.submissions:
                self.assertTrue(prev < submission.created_utc)
                prev = submission.created_utc

    def test_recent_type_eror(self):
        self.assertRaises(TypeError, self.srs.fetch_recent_submissions,
                          exclude_self=True, exclude_link=True, after=None,
                          max_duration=7)

    @mock.patch('time.sleep', return_value=None)
    def test_top(self, _sleep_mock):
        with self.recorder.use_cassette('StatsTest.test_top'):
            self.assertTrue(
                self.srs.fetch_top_submissions('week', None, None))
            self.assertTrue(len(self.srs.submissions) > 1)
            prev = 0
            for submission in self.srs.submissions:
                self.assertTrue(prev < submission.created_utc)
                prev = submission.created_utc

    def test_top_type_eror(self):
        self.assertRaises(TypeError, self.srs.fetch_top_submissions,
                          exclude_self=True, exclude_link=True)
