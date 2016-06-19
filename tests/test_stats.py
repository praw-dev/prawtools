import unittest
from prawtools.stats import SubRedditStats


class StatsTest(unittest.TestCase):
    def test_recent(self):
        srs = SubRedditStats('redditdev', None, None, None)
        self.assertTrue(
            srs.fetch_recent_submissions(max_duration=7,
                                         after=None,
                                         exclude_self=False,
                                         exclude_link=False))
        self.assertTrue(len(srs.submissions) > 1)
        prev = 0
        for submission in srs.submissions:
            self.assertTrue(prev < submission.created_utc)
            prev = submission.created_utc

    def test_recent_type_eror(self):
        srs = SubRedditStats('redditdev', None, None, None)
        self.assertRaises(TypeError, srs.fetch_recent_submissions,
                          exclude_self=True, exclude_link=True, after=None,
                          max_duration=7)

    def test_top(self):
        srs = SubRedditStats('redditdev', None, None, None)
        self.assertTrue(
            srs.fetch_top_submissions('week', None, None))
        self.assertTrue(len(srs.submissions) > 1)
        prev = 0
        for submission in srs.submissions:
            self.assertTrue(prev < submission.created_utc)
            prev = submission.created_utc

    def test_top_type_eror(self):
        srs = SubRedditStats('redditdev', None, None, None)
        self.assertRaises(TypeError, srs.fetch_top_submissions,
                          exclude_self=True, exclude_link=True)
