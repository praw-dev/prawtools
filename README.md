Introduction
---

subreddit_stats.py is a tool to provide basic statistics on a subreddit.
To see the what sort of output subreddit stats generates check out
[/r/subreddit_stats](http://www.reddit.com/r/subreddit_stats).

subreddit_stats.py depends on
[the python reddit api wrapper](/mellort/reddit_api).

Examples
---

0. Generate stats for subreddit __foo__ for the last 30 days with extra
verbose output. Post results to subreddit __bar__ as user __user__.

    ```
./subreddit_stats.py -d30 -vv -R bar -u user foo
```
