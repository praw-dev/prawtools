#!/usr/bin/env python
import re
import sys
import time
from collections import defaultdict
from datetime import datetime
from praw import Reddit
from praw.errors import ExceptionList, RateLimitExceeded
from praw.objects import Redditor
from six import iteritems, itervalues, text_type as tt
from .helpers import arg_parser

DAYS_IN_SECONDS = 60 * 60 * 24
MAX_BODY_SIZE = 10000


def safe_title(submission):
    return submission.title.replace('\n', ' ').strip()


class SubRedditStats(object):
    post_prefix = tt('Subreddit Stats:')
    post_header = tt('---\n###{0}\n')
    post_footer = tt('>Generated with [BBoe](/u/bboe)\'s [Subreddit Stats]'
                     '(https://github.com/praw-dev/prawtools)  \n{0}'
                     'SRS Marker: {1}')
    re_marker = re.compile('SRS Marker: (\d+)')

    @staticmethod
    def _previous_max(submission):
        try:
            val = SubRedditStats.re_marker.findall(submission.selftext)[-1]
            return float(val)
        except (IndexError, TypeError):
            print('End marker not found in previous submission. Aborting')
            sys.exit(1)

    @staticmethod
    def _permalink(permalink):
        tokens = permalink.split('/')
        if tokens[8] == '':  # submission
            return tt('/comments/{0}/_/').format(tokens[6])
        else:  # comment
            return tt('/comments/{0}/_/{1}?context=1').format(tokens[6],
                                                              tokens[8])

    @staticmethod
    def _user(user):
        if user is None:
            return '_deleted_'
        elif isinstance(user, Redditor):
            user = str(user)
        return tt('[{0}](/user/{1})').format(user.replace('_', '\_'), user)

    @staticmethod
    def _submit(func, *args, **kwargs):
        def sleep(sleep_time):
            print('\tSleeping for {0} seconds'.format(sleep_time))
            time.sleep(sleep_time)

        while True:
            try:
                return func(*args, **kwargs)
            except RateLimitExceeded as error:
                sleep(error.sleep_time)
            except ExceptionList as exception_list:
                for error in exception_list.errors:
                    if isinstance(error, RateLimitExceeded):
                        sleep(error.sleep_time)
                        break
                else:
                    raise

    def __init__(self, subreddit, site, verbosity):
        self.reddit = Reddit(str(self), site)
        self.subreddit = self.reddit.get_subreddit(subreddit)
        self.verbosity = verbosity
        self.submissions = []
        self.comments = []
        self.submitters = defaultdict(list)
        self.commenters = defaultdict(list)
        self.min_date = 0
        self.max_date = time.time() - DAYS_IN_SECONDS * 3
        self.prev_srs = None
        # Config
        self.reddit.config.comment_limit = -1  # Fetch max comments possible
        self.reddit.config.comment_sort = 'top'

    def login(self, user, pswd):
        if self.verbosity > 0:
            print('Logging in')
        self.reddit.login(user, pswd)

    def msg(self, msg, level, overwrite=False):
        if self.verbosity >= level:
            sys.stdout.write(msg)
            if overwrite:
                sys.stdout.write('\r')
                sys.stdout.flush()
            else:
                sys.stdout.write('\n')

    def prev_stat(self, prev_url):
        submission = self.reddit.get_submission(prev_url)
        self.min_date = self._previous_max(submission)
        self.prev_srs = prev_url

    def fetch_recent_submissions(self, max_duration, after, exclude_self,
                                 since_last=True):
        '''Fetches recent submissions in subreddit with boundaries.

        Does not include posts within the last three days as their scores may
        not be representative.

        Keyword arguments:
        max_duration -- When set, specifies the number of days to include
        after -- When set, fetch all submission after this submission id.
        exclude_self -- When true, don't include self posts.
        since_last -- When true use info from last submission to determine the
                      stop point
        '''
        if max_duration:
            self.min_date = self.max_date - DAYS_IN_SECONDS * max_duration
        url_data = {'after': after} if after else None
        self.msg('DEBUG: Fetching submissions', 1)
        for submission in self.subreddit.get_new_by_date(limit=None,
                                                         url_data=url_data):
            if submission.created_utc > self.max_date:
                continue
            if submission.created_utc <= self.min_date:
                break
            if (since_last and str(submission.author) == str(self.reddit.user)
                and submission.title.startswith(self.post_prefix)):
                # Use info in this post to update the min_date
                # And don't include this post
                self.msg(tt('Found previous: {0}')
                         .format(safe_title(submission)), 2)
                if self.prev_srs is None:  # Only use the most recent
                    self.min_date = max(self.min_date,
                                        self._previous_max(submission))
                    self.prev_srs = submission.permalink
                continue
            if exclude_self and submission.is_self:
                continue
            self.submissions.append(submission)
        num_submissions = len(self.submissions)
        self.msg('DEBUG: Found {0} submissions'.format(num_submissions), 1)
        if num_submissions == 0:
            return False

        # Update real min and max dates
        self.submissions.sort(key=lambda x: x.created_utc)
        self.min_date = self.submissions[0].created_utc
        self.max_date = self.submissions[-1].created_utc
        return True

    def fetch_top_submissions(self, top, exclude_self):
        '''Fetches top 1000 submissions by some top value.

        Keyword arguments:
        top -- One of week, month, year, all
        exclude_self -- When true, don't include self posts.
        '''
        if top not in ('day', 'week', 'month', 'year', 'all'):
            raise TypeError('{0!r} is not a valid top value'.format(top))
        self.msg('DEBUG: Fetching submissions', 1)
        url_data = {'t': top}
        for submission in self.subreddit.get_top(limit=None,
                                                 url_data=url_data):
            if exclude_self and submission.is_self:
                continue
            self.submissions.append(submission)
        num_submissions = len(self.submissions)
        self.msg('DEBUG: Found {0} submissions'.format(num_submissions), 1)
        if num_submissions == 0:
            return False

        # Update real min and max dates
        self.submissions.sort(key=lambda x: x.created_utc)
        self.min_date = self.submissions[0].created_utc
        self.max_date = self.submissions[-1].created_utc
        return True

    def process_submitters(self):
        self.msg('DEBUG: Processing Submitters', 1)
        for submission in self.submissions:
            if submission.author:
                self.submitters[str(submission.author)].append(submission)

    def process_commenters(self):
        num = len(self.submissions)
        self.msg('DEBUG: Processing Commenters on {0} submissions'.format(num),
                 1)
        for i, submission in enumerate(self.submissions):
            self.msg('{0}/{1} submissions'.format(i + 1, num), 2,
                     overwrite=True)
            if submission.num_comments == 0:
                continue
            try:
                self.comments.extend(submission.all_comments_flat)
            except Exception as exception:
                print('Exception fetching comments on {0!r}: {1}'.format(
                        submission.content_id, str(exception)))
            for orphans in itervalues(submission._orphaned):
                self.comments.extend(orphans)
        for comment in self.comments:
            if comment.author:
                self.commenters[str(comment.author)].append(comment)

    def basic_stats(self):
        sub_ups = sum(x.ups for x in self.submissions)
        sub_downs = sum(x.downs for x in self.submissions)
        comm_ups = sum(x.ups for x in self.comments)
        comm_downs = sum(x.downs for x in self.comments)

        if sub_ups > 0 or sub_downs > 0:
            sub_up_perc = sub_ups * 100 / (sub_ups + sub_downs)
        else:
            sub_up_perc = 100
        if comm_ups > 0 or comm_downs > 0:
            comm_up_perc = comm_ups * 100 / (comm_ups + comm_downs)
        else:
            comm_up_perc = 100

        values = [('Total', len(self.submissions), '', len(self.comments), ''),
                  ('Unique Redditors', len(self.submitters), '',
                   len(self.commenters), ''),
                  ('Upvotes', sub_ups, '{0}%'.format(sub_up_perc),
                   comm_ups, '{0}%'.format(comm_up_perc)),
                  ('Downvotes', sub_downs, '{0}%'.format(100 - sub_up_perc),
                   comm_downs, '{0}%'.format(100 - comm_up_perc))]

        retval = '||Submissions|%|Comments|%|\n:-:|--:|--:|--:|--:\n'
        for quad in values:
            retval += '__{0}__|{1}|{2}|{3}|{4}\n'.format(*quad)
        return retval + '\n'

    def top_submitters(self, num, num_submissions):
        num = min(num, len(self.submitters))
        if num <= 0:
            return ''

        top_submitters = sorted(iteritems(self.submitters), reverse=True,
                                key=lambda x: (sum(y.score for y in x[1]),
                                               len(x[1])))[:num]

        retval = self.post_header.format('Top Submitters\' Top Submissions')
        for (author, submissions) in top_submitters:
            retval += '0. {0} pts, {1} submissions: {2}\n'.format(
                sum(x.score for x in submissions), len(submissions),
                self._user(author))
            for sub in sorted(submissions, reverse=True,
                              key=lambda x: x.score)[:num_submissions]:
                title = safe_title(sub)
                if sub.permalink != sub.url:
                    retval += tt('  0. [{0}]({1})').format(title, sub.url)
                else:
                    retval += tt('  0. {0}').format(title)
                retval += ' ({0} pts, [{1} comments]({2}))\n'.format(
                    sub.score, sub.num_comments,
                    self._permalink(sub.permalink))
            retval += '\n'
        return retval

    def top_commenters(self, num):
        score = lambda x: x.ups - x.downs

        num = min(num, len(self.commenters))
        if num <= 0:
            return ''

        top_commenters = sorted(iteritems(self.commenters), reverse=True,
                                key=lambda x: (sum(score(y) for y in x[1]),
                                               len(x[1])))[:num]

        retval = self.post_header.format('Top Commenters')
        for author, comments in top_commenters:
            retval += '0. {0} ({1} pts, {2} comments)\n'.format(
                self._user(author), sum(score(x) for x in comments),
                len(comments))
        return '{0}\n'.format(retval)

    def top_submissions(self, num):
        num = min(num, len(self.submissions))
        if num <= 0:
            return ''

        top_submissions = sorted(self.submissions, reverse=True,
                                 key=lambda x: x.score)[:num]

        retval = self.post_header.format('Top Submissions')
        for sub in top_submissions:
            title = safe_title(sub)
            if sub.permalink != sub.url:
                retval += tt('0. [{0}]({1})').format(title, sub.url)
            else:
                retval += tt('0. {0}').format(title)
            retval += ' by {0} ({1} pts, [{2} comments]({3}))\n'.format(
                self._user(sub.author), sub.score, sub.num_comments,
                self._permalink(sub.permalink))
        return tt('{0}\n').format(retval)

    def top_comments(self, num):
        score = lambda x: x.ups - x.downs

        num = min(num, len(self.comments))
        if num <= 0:
            return ''

        top_comments = sorted(self.comments, reverse=True,
                              key=score)[:num]
        retval = self.post_header.format('Top Comments')
        for comment in top_comments:
            title = safe_title(comment.submission)
            retval += tt('0. {0} pts: {1}\'s [comment]({2}) in {3}\n').format(
                score(comment), self._user(comment.author),
                self._permalink(comment.permalink), title)
        return tt('{0}\n').format(retval)

    def publish_results(self, subreddit, submitters, commenters, submissions,
                        comments, top, debug=False):
        def timef(timestamp, date_only=False):
            dtime = datetime.fromtimestamp(timestamp)
            if date_only:
                retval = dtime.strftime('%Y-%m-%d')
            else:
                retval = dtime.strftime('%Y-%m-%d %H:%M PDT')
            return retval

        if self.prev_srs:
            prev = '[Prev SRS]({0})  \n'.format(self._permalink(self.prev_srs))
        else:
            prev = ''

        basic = self.basic_stats()
        t_commenters = self.top_commenters(commenters)
        t_submissions = self.top_submissions(submissions)
        t_comments = self.top_comments(comments)
        footer = self.post_footer.format(prev, self.max_date)

        body = ''
        num_submissions = 10
        while body == '' or len(body) > MAX_BODY_SIZE and num_submissions > 2:
            t_submitters = self.top_submitters(submitters, num_submissions)
            body = (basic + t_submitters + t_commenters + t_submissions +
                    t_comments + footer)
            num_submissions -= 1

        if len(body) > MAX_BODY_SIZE:
            print('The resulting message is too big. Not submitting.')
            debug = True

        # Set the initial title
        base_title = '{0} {1} {2}posts from {3} to {4}'.format(
            self.post_prefix, str(self.subreddit),
            'top ' if top else '', timef(self.min_date, True),
            timef(self.max_date))

        submitted = False
        while not debug and not submitted:
            if subreddit:  # Verify the user wants to submit to the subreddit
                msg = ('You are about to submit to subreddit {0!r} as {1!r}.\n'
                       'Are you sure? yes/[no]: '.format(
                        subreddit, str(self.reddit.user)))
                sys.stdout.write(msg)
                sys.stdout.flush()
                if sys.stdin.readline().strip().lower() not in ['y', 'yes']:
                    subreddit = None
            elif not subreddit:  # Prompt for the subreddit to submit to
                msg = ('Please enter a subreddit to submit to (press return to'
                       ' abort): ')
                sys.stdout.write(msg)
                sys.stdout.flush()
                subreddit = sys.stdin.readline().strip()
                if not subreddit:
                    print('Submission aborted\n')
                    debug = True

            # Vary the title depending on where posting
            if str(self.subreddit) == subreddit:
                title = '{0} {1}posts from {2} to {3}'.format(
                    self.post_prefix, 'top ' if top else '',
                    timef(self.min_date, True), timef(self.max_date))
            else:
                title = base_title

            if subreddit:
                # Attempt to make the submission
                try:
                    res = self._submit(self.reddit.submit, subreddit, title,
                                       text=body)
                    print(res.permalink)
                    submitted = True
                except Exception as error:
                    raise
                    print('The submission failed:' + str(error))
                    subreddit = None

        if not submitted:
            print(base_title)
            print(body)


def main():
    parser = arg_parser(usage='usage: %prog [options] subreddit')
    parser.add_option('-s', '--submitters', type='int', default=5,
                      help='Number of top submitters to display '
                      '[default %default]')
    parser.add_option('-c', '--commenters', type='int', default=10,
                      help='Number of top commenters to display '
                      '[default %default]')
    parser.add_option('-a', '--after',
                      help='Submission ID to fetch after')
    parser.add_option('-d', '--days', type='int', default=32,
                      help=('Number of previous days to include submissions '
                            'from. Use 0 for unlimited. Default: %default'))
    parser.add_option('-D', '--debug', action='store_true',
                      help='Enable debugging mode. Does not post stats.')
    parser.add_option('-R', '--submission-reddit',
                      help=('Subreddit to submit to. If not present, '
                            'submits to the subreddit processed'))
    parser.add_option('-t', '--top',
                      help=('Run on top submissions either by day, week, '
                            'month, year, or all'))
    parser.add_option('', '--no-self', action='store_true',
                      help=('Do not include self posts (and their comments) in'
                            ' the calculation. '))
    parser.add_option('', '--prev',
                      help='Statically provide the URL of previous SRS page.')
    parser.add_option('', '--include-prev', action='store_true',
                      help='Don\'t try to avoid overlap with a previous SRS.')

    options, args = parser.parse_args()
    if len(args) != 1:
        parser.error('Must provide subreddit')

    if options.submission_reddit:
        submission_reddit = options.submission_reddit
    else:
        submission_reddit = args[0]

    srs = SubRedditStats(args[0], options.site, options.verbose)
    srs.login(options.user, options.pswd)
    if options.prev:
        srs.prev_stat(options.prev)
    if options.top:
        found = srs.fetch_top_submissions(options.top, options.no_self)
    else:
        since_last = not options.include_prev
        found = srs.fetch_recent_submissions(max_duration=options.days,
                                             after=options.after,
                                             exclude_self=options.no_self,
                                             since_last=since_last)
    if not found:
        print('No submissions were found.')
        return 1
    srs.process_submitters()
    if options.commenters > 0:
        srs.process_commenters()
    srs.publish_results(submission_reddit, options.submitters,
                        options.commenters, 5, 5, options.top, options.debug)
