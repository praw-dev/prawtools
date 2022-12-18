"""Test subreddit_stats."""
import mock
from prawtools.stats import SubredditStats

from . import IntegrationTest


class StatsTest(IntegrationTest):
    def setUp(self):
        """Setup runs before all test cases."""
        self.srs = SubredditStats("redditdev", None, None, None)
        super(StatsTest, self).setUp(self.srs.reddit._core._requestor._http)

    def test_recent(self):
        with self.recorder.use_cassette("StatsTest.recent"):
            self.srs.max_date = 1466000000  # To work with current cassette
            self.srs.fetch_recent_submissions(7)
            self.assertTrue(len(self.srs.submissions) > 1)

    @mock.patch("time.sleep", return_value=None)
    def test_top(self, _sleep_mock):
        with self.recorder.use_cassette("StatsTest.top"):
            self.srs.fetch_top_submissions("week")
            self.assertTrue(len(self.srs.submissions) > 1)
