Introduction
---

Reddit Modutils is a tool to assist Reddit community moderators in moderating
their community. At present, it is mostly useful for automatically building
flair templates from existing user flair, however, it can also be used to
quickly list banned users, contributors, and moderators.

Examples
---

Note: all examples require you to be a moderator for the subreddit

0. List banned users for subreddit __foo__

    ```
./modutils.py -l banned foo
```

0. Get current flair for subreddit __bar__

    ```
./modutils.py -f bar
```

0. Synchronize flair templates with existing flair for subreddit __baz__,
building non-editable templates for any flair whose flair-text is common among
at least 2 users.

    ```
./modutils.py --sync --ignore-css --limit=2 baz
```
