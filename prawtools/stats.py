"""Utility to provide submission and comment statistics in a subreddit."""
from __future__ import print_function
from collections import defaultdict
from datetime import datetime
from tempfile import mkstemp
import codecs
import gc
import logging
import os
import re
import time


from praw import Reddit
from prawcore.exceptions import RequestException
from six import iteritems, text_type as tt

from .helpers import AGENT, arg_parser, check_for_updates

SECONDS_IN_A_DAY = 60 * 60 * 24
RE_WHITESPACE = re.compile(r"\s+")
TOP_VALUES = {"all", "day", "month", "week", "year"}

logger = logging.getLogger(__package__)


class MiniComment(object):
    """Provides a memory optimized version of a Comment."""

    __slots__ = ("author", "created_utc", "id", "score", "submission")

    def __init__(self, comment, submission):
        """Initialize an instance of MiniComment."""
        for attribute in self.__slots__:
            if attribute in {"author", "submission"}:
                continue
            setattr(self, attribute, getattr(comment, attribute))
        self.author = str(comment.author) if comment.author else None
        self.submission = submission


class MiniSubmission(object):
    """Provides a memory optimized version of a Submission."""

    __slots__ = (
        "author",
        "created_utc",
        "distinguished",
        "id",
        "num_comments",
        "permalink",
        "score",
        "title",
        "url",
    )

    def __init__(self, submission):
        """Initialize an instance of MiniSubmission."""
        for attribute in self.__slots__:
            if attribute == "author":
                continue
            setattr(self, attribute, getattr(submission, attribute))
        self.author = str(submission.author) if submission.author else None


class SubredditStats(object):
    """Contain all the functionality of the subreddit_stats command."""

    post_footer = tt(
        ">Generated with [BBoe](/u/bboe)'s [Subreddit Stats]"
        "(https://github.com/praw-dev/prawtools)"
    )
    post_header = tt("---\n###{}\n")
    post_prefix = tt("Subreddit Stats:")

    @staticmethod
    def _permalink(item):
        if isinstance(item, MiniSubmission):
            return tt("/comments/{}").format(item.id)
        else:
            return tt("/comments/{}/_/{}?context=1").format(item.submission.id, item.id)

    @staticmethod
    def _points(points):
        return "1 point" if points == 1 else "{} points".format(points)

    @staticmethod
    def _rate(items, duration):
        return 86400.0 * items / duration if duration else items

    @staticmethod
    def _safe_title(submission):
        """Return titles with whitespace replaced by spaces and stripped."""
        return RE_WHITESPACE.sub(" ", submission.title).strip()

    @staticmethod
    def _save_report(title, body):
        descriptor, filename = mkstemp(".md", dir=".")
        os.close(descriptor)
        with codecs.open(filename, "w", "utf-8") as fp:
            fp.write("{}\n\n{}".format(title, body))
        logger.info("Report saved to {}".format(filename))

    @staticmethod
    def _user(user):
        return "_deleted_" if user is None else tt("/u/{}").format(user)

    def __init__(self, subreddit, site, distinguished, reddit=None):
        """Initialize the SubredditStats instance with config options."""
        self.commenters = defaultdict(list)
        self.comments = []
        self.distinguished = distinguished
        self.min_date = 0
        self.max_date = time.time() - SECONDS_IN_A_DAY
        self.reddit = reddit or Reddit(site, check_for_updates=False, user_agent=AGENT)
        self.submissions = {}
        self.submitters = defaultdict(list)
        self.submit_subreddit = self.reddit.subreddit("subreddit_stats")
        self.subreddit = self.reddit.subreddit(subreddit)

    def basic_stats(self):
        """Return a markdown representation of simple statistics."""
        comment_score = sum(comment.score for comment in self.comments)
        if self.comments:
            comment_duration = (
                self.comments[-1].created_utc - self.comments[0].created_utc
            )
            comment_rate = self._rate(len(self.comments), comment_duration)
        else:
            comment_rate = 0

        submission_duration = self.max_date - self.min_date
        submission_rate = self._rate(len(self.submissions), submission_duration)
        submission_score = sum(sub.score for sub in self.submissions.values())

        values = [
            ("Total", len(self.submissions), len(self.comments)),
            (
                "Rate (per day)",
                "{:.2f}".format(submission_rate),
                "{:.2f}".format(comment_rate),
            ),
            ("Unique Redditors", len(self.submitters), len(self.commenters)),
            ("Combined Score", submission_score, comment_score),
        ]

        retval = "Period: {:.2f} days\n\n".format(submission_duration / 86400.0)
        retval += "||Submissions|Comments|\n:-:|--:|--:\n"
        for quad in values:
            retval += "__{}__|{}|{}\n".format(*quad)
        return retval + "\n"

    def fetch_recent_submissions(self, max_duration):
        """Fetch recent submissions in subreddit with boundaries.

        Does not include posts within the last day as their scores may not be
        representative.

        :param max_duration: When set, specifies the number of days to include

        """
        if max_duration:
            self.min_date = self.max_date - SECONDS_IN_A_DAY * max_duration
        for submission in self.subreddit.new(limit=None):
            if submission.created_utc <= self.min_date:
                break
            if submission.created_utc > self.max_date:
                continue
            self.submissions[submission.id] = MiniSubmission(submission)

    def fetch_submissions(self, submissions_callback, *args):
        """Wrap the submissions_callback function."""
        logger.debug("Fetching submissions")

        submissions_callback(*args)

        logger.info("Found {} submissions".format(len(self.submissions)))
        if not self.submissions:
            return

        self.min_date = min(x.created_utc for x in self.submissions.values())
        self.max_date = max(x.created_utc for x in self.submissions.values())

        self.process_submitters()
        self.process_commenters()

    def fetch_top_submissions(self, top):
        """Fetch top submissions by some top value.

        :param top: One of week, month, year, all
        :returns: True if any submissions were found.

        """
        for submission in self.subreddit.top(limit=None, time_filter=top):
            self.submissions[submission.id] = MiniSubmission(submission)

    def process_commenters(self):
        """Group comments by author."""
        for index, submission in enumerate(self.submissions.values()):
            if submission.num_comments == 0:
                continue
            real_submission = self.reddit.submission(id=submission.id)
            real_submission.comment_sort = "top"

            for i in range(3):
                try:
                    real_submission.comments.replace_more(limit=0)
                    break
                except RequestException:
                    if i >= 2:
                        raise
                    logger.debug(
                        "Failed to fetch submission {}, retrying".format(submission.id)
                    )

            self.comments.extend(
                MiniComment(comment, submission)
                for comment in real_submission.comments.list()
                if self.distinguished or comment.distinguished is None
            )

            if index % 50 == 49:
                logger.debug(
                    "Completed: {:4d}/{} submissions".format(
                        index + 1, len(self.submissions)
                    )
                )

            # Clean up to reduce memory usage
            submission = None
            gc.collect()

        self.comments.sort(key=lambda x: x.created_utc)
        for comment in self.comments:
            if comment.author:
                self.commenters[comment.author].append(comment)

    def process_submitters(self):
        """Group submissions by author."""
        for submission in self.submissions.values():
            if submission.author and (
                self.distinguished or submission.distinguished is None
            ):
                self.submitters[submission.author].append(submission)

    def publish_results(self, view, submitters, commenters):
        """Submit the results to the subreddit. Has no return value (None)."""

        def timef(timestamp, date_only=False):
            """Return a suitable string representaation of the timestamp."""
            dtime = datetime.fromtimestamp(timestamp)
            if date_only:
                retval = dtime.strftime("%Y-%m-%d")
            else:
                retval = dtime.strftime("%Y-%m-%d %H:%M PDT")
            return retval

        basic = self.basic_stats()
        top_commenters = self.top_commenters(commenters)
        top_comments = self.top_comments()
        top_submissions = self.top_submissions()

        # Decrease number of top submitters if body is too large.
        body = None
        while body is None or len(body) > 40000 and submitters > 0:
            body = (
                basic
                + self.top_submitters(submitters)
                + top_commenters
                + top_submissions
                + top_comments
                + self.post_footer
            )
            submitters -= 1

        title = "{} {} {}posts from {} to {}".format(
            self.post_prefix,
            str(self.subreddit),
            "top " if view in TOP_VALUES else "",
            timef(self.min_date, True),
            timef(self.max_date),
        )

        try:  # Attempt to make the submission
            return self.submit_subreddit.submit(title, selftext=body)
        except Exception:
            logger.exception("Failed to submit to {}".format(self.submit_subreddit))
            self._save_report(title, body)

    def run(self, view, submitters, commenters):
        """Run stats and return the created Submission."""
        logger.info("Analyzing subreddit: {}".format(self.subreddit))

        if view in TOP_VALUES:
            callback = self.fetch_top_submissions
        else:
            callback = self.fetch_recent_submissions
            view = int(view)
        self.fetch_submissions(callback, view)

        if not self.submissions:
            logger.warning("No submissions were found.")
            return

        return self.publish_results(view, submitters, commenters)

    def top_commenters(self, num):
        """Return a markdown representation of the top commenters."""
        num = min(num, len(self.commenters))
        if num <= 0:
            return ""

        top_commenters = sorted(
            iteritems(self.commenters),
            key=lambda x: (-sum(y.score for y in x[1]), -len(x[1]), str(x[0])),
        )[:num]

        retval = self.post_header.format("Top Commenters")
        for author, comments in top_commenters:
            retval += "1. {} ({}, {} comment{})\n".format(
                self._user(author),
                self._points(sum(x.score for x in comments)),
                len(comments),
                "s" if len(comments) != 1 else "",
            )
        return "{}\n".format(retval)

    def top_submitters(self, num):
        """Return a markdown representation of the top submitters."""
        num = min(num, len(self.submitters))
        if num <= 0:
            return ""

        top_submitters = sorted(
            iteritems(self.submitters),
            key=lambda x: (-sum(y.score for y in x[1]), -len(x[1]), str(x[0])),
        )[:num]

        retval = self.post_header.format("Top Submitters' Top Submissions")
        for (author, submissions) in top_submitters:
            retval += "1. {}, {} submission{}: {}\n".format(
                self._points(sum(x.score for x in submissions)),
                len(submissions),
                "s" if len(submissions) != 1 else "",
                self._user(author),
            )
            for sub in sorted(submissions, key=lambda x: (-x.score, x.title))[:10]:
                title = self._safe_title(sub)
                if sub.permalink in sub.url:
                    retval += tt("    1. {}").format(title)
                else:
                    retval += tt("    1. [{}]({})").format(title, sub.url)
                retval += " ({}, [{} comment{}]({}))\n".format(
                    self._points(sub.score),
                    sub.num_comments,
                    "s" if sub.num_comments != 1 else "",
                    self._permalink(sub),
                )
            retval += "\n"
        return retval

    def top_submissions(self):
        """Return a markdown representation of the top submissions."""
        num = min(10, len(self.submissions))
        if num <= 0:
            return ""

        top_submissions = sorted(
            [
                x
                for x in self.submissions.values()
                if self.distinguished or x.distinguished is None
            ],
            key=lambda x: (-x.score, -x.num_comments, x.title),
        )[:num]

        if not top_submissions:
            return ""

        retval = self.post_header.format("Top Submissions")
        for sub in top_submissions:
            title = self._safe_title(sub)
            if sub.permalink in sub.url:
                retval += tt("1. {}").format(title)
            else:
                retval += tt("1. [{}]({})").format(title, sub.url)

            retval += " by {} ({}, [{} comment{}]({}))\n".format(
                self._user(sub.author),
                self._points(sub.score),
                sub.num_comments,
                "s" if sub.num_comments != 1 else "",
                self._permalink(sub),
            )
        return tt("{}\n").format(retval)

    def top_comments(self):
        """Return a markdown representation of the top comments."""
        num = min(10, len(self.comments))
        if num <= 0:
            return ""

        top_comments = sorted(self.comments, key=lambda x: (-x.score, str(x.author)))[
            :num
        ]
        retval = self.post_header.format("Top Comments")
        for comment in top_comments:
            title = self._safe_title(comment.submission)
            retval += tt("1. {}: {}'s [comment]({}) in {}\n").format(
                self._points(comment.score),
                self._user(comment.author),
                self._permalink(comment),
                title,
            )
        return tt("{}\n").format(retval)


def main():
    """Provide the entry point to the subreddit_stats command."""
    parser = arg_parser(usage="usage: %prog [options] SUBREDDIT VIEW")
    parser.add_option(
        "-c",
        "--commenters",
        type="int",
        default=10,
        help="Number of top commenters to display " "[default %default]",
    )
    parser.add_option(
        "-d",
        "--distinguished",
        action="store_true",
        help=(
            "Include distinguished subissions and "
            "comments (default: False). Note that regular "
            "comments of distinguished submissions will still "
            "be included."
        ),
    )
    parser.add_option(
        "-s",
        "--submitters",
        type="int",
        default=10,
        help="Number of top submitters to display " "[default %default]",
    )

    options, args = parser.parse_args()

    if options.verbose == 1:
        logger.setLevel(logging.INFO)
    elif options.verbose > 1:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.NOTSET)
    logger.addHandler(logging.StreamHandler())

    if len(args) != 2:
        parser.error("SUBREDDIT and VIEW must be provided")
    subreddit, view = args
    check_for_updates(options)
    srs = SubredditStats(subreddit, options.site, options.distinguished)
    result = srs.run(view, options.submitters, options.commenters)
    if result:
        print(result.permalink)
    return 0
