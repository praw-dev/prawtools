#!/usr/bin/env python
import unittest
from prawtools.stats import SubRedditStats


class StatsTest(unittest.TestCase):  # pylint: disable-msg=R0904
    def test_recent(self):
        srs = SubRedditStats('redditdev', None, None)
        self.assertTrue(
            srs.fetch_recent_submissions(7, None, None, None))
        self.assertTrue(len(srs.submissions) > 1)
        prev = 0
        for submission in srs.submissions:
            self.assertTrue(prev < submission.created_utc)
            prev = submission.created_utc

    def test_top(self):
        srs = SubRedditStats('redditdev', None, None)
        self.assertTrue(
            srs.fetch_top_submissions('week', None))
        self.assertTrue(len(srs.submissions) > 1)
        prev = 0
        for submission in srs.submissions:
            self.assertTrue(prev < submission.created_utc)
            prev = submission.created_utc


if __name__ == '__main__':
    unittest.main()
