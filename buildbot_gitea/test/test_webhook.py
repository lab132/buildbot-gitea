import buildbot.www.change_hook as change_hook
from buildbot.test.fake.web import FakeRequest
from buildbot.test.fake.web import fakeMasterForHooks
from buildbot.test.util.misc import TestReactorMixin



from twisted.internet import defer
from twisted.trial import unittest

from buildbot_gitea.webhook import GiteaHandler, _HEADER_EVENT_TYPE

giteaJsonPushPayload = rb"""
{
  "secret": "test",
  "ref": "refs/heads/feature-branch",
  "before": "0000000000000000000000000000000000000000",
  "after": "9d7157cc4a137b3e1dfe92750ccfb1bbad239f99",
  "compare_url": "https://git.example.com/",
  "commits": [
    {
      "id": "9d7157cc4a137b3e1dfe92750ccfb1bbad239f99",
      "message": "TestBranch\n",
      "url": "https://git.example.com/max/webhook_test/commit/9d7157cc4a137b3e1dfe92750ccfb1bbad239f99",
      "author": {
        "name": "Max Mustermann",
        "email": "max@example.com",
        "username": "max"
      },
      "committer": {
        "name": "Max Mustermann",
        "email": "max@example.com",
        "username": "max"
      },
      "verification": null,
      "timestamp": "2018-09-04T12:10:14Z"
    },
    {
      "id": "ad7157cc4a137b3e1dfe92750ccfb1bbad239f9a",
      "message": "TestBranch2\n",
      "url": "https://git.example.com/max/webhook_test/commit/ad7157cc4a137b3e1dfe92750ccfb1bbad239f9a",
      "author": {
        "name": "Max Mustermann",
        "email": "max@example.com",
        "username": "max"
      },
      "committer": {
        "name": "Max Mustermann",
        "email": "max@example.com",
        "username": "max"
      },
      "verification": null,
      "timestamp": "2018-09-04T12:10:14Z"
    }
  ],
  "repository": {
    "id": 20,
    "owner": {
      "id": 1,
      "login": "max",
      "full_name": "Max Mustermann",
      "email": "max@example.com",
      "avatar_url": "https://secure.gravatar.com/avatar/c9a5fca94b7fd6f8d4dbab8d1575e4fc?d=identicon",
      "language": "en-US",
      "username": "max"
    },
    "name": "webhook_test",
    "full_name": "max/webhook_test",
    "description": "",
    "empty": false,
    "private": true,
    "fork": false,
    "parent": null,
    "mirror": false,
    "size": 48,
    "html_url": "https://git.example.com/max/webhook_test",
    "ssh_url": "ssh://git@git.example.com/max/webhook_test.git",
    "clone_url": "https://git.example.com/max/webhook_test.git",
    "website": "",
    "stars_count": 0,
    "forks_count": 0,
    "watchers_count": 1,
    "open_issues_count": 0,
    "default_branch": "master",
    "created_at": "2018-09-04T10:45:23Z",
    "updated_at": "2018-09-04T12:10:14Z",
    "permissions": {
      "admin": false,
      "push": false,
      "pull": false
    }
  },
  "pusher": {
    "id": 1,
    "login": "max",
    "full_name": "Max Mustermann",
    "email": "max@example.com",
    "avatar_url": "https://secure.gravatar.com/avatar/c9a5fca94b7fd6f8d4dbab8d1575e4fc?d=identicon",
    "language": "en-US",
    "username": "max"
  },
  "sender": {
    "id": 1,
    "login": "max",
    "full_name": "Max Mustermann",
    "email": "max@example.com",
    "avatar_url": "https://secure.gravatar.com/avatar/c9a5fca94b7fd6f8d4dbab8d1575e4fc?d=identicon",
    "language": "en-US",
    "username": "max"
  }
}
"""

giteaJsonPushModifiedFiles = rb"""
{
  "secret": "pass",
  "ref": "refs/heads/master",
  "before": "92a8bf0e02b2146e6b35b71d6e08c376133b7fc9",
  "after": "ea07c3148db428876add8b312256239275c395fb",
  "compare_url": "https://git.example.com/Test/test/compare/92a8bf0e02b2146e6b35b71d6e08c376133b7fc9...ea07c3148db428876add8b312256239275c395fb",
  "commits": [
    {
      "id": "ea07c3148db428876add8b312256239275c395fb",
      "message": "test123\n",
      "url": "https://git.example.com/Test/test/commit/ea07c3148db428876add8b312256239275c395fb",
      "author": {
        "name": "Test User",
        "email": "Test@example.com",
        "username": "Test"
      },
      "committer": {
        "name": "Test User",
        "email": "Test@example.com",
        "username": "Test"
      },
      "verification": null,
      "timestamp": "2021-03-09T20:12:19Z",
      "added": [
        "testfile2"
      ],
      "removed": [
        "testfile3"
      ],
      "modified": [
        "testfile1"
      ]
    }
  ],
  "head_commit": null,
  "repository": {
    "id": 29,
    "owner": {
      "id": 1,
      "login": "Test",
      "full_name": "Test User",
      "email": "Test@example.com",
      "avatar_url": "https://git.example.com/user/avatar/Test/-1",
      "language": "en-US",
      "is_admin": true,
      "last_login": "2021-03-09T20:10:52Z",
      "created": "2018-06-05T09:41:06Z",
      "username": "Test"
    },
    "name": "test",
    "full_name": "Test/test",
    "description": "",
    "empty": false,
    "private": true,
    "fork": false,
    "template": false,
    "parent": null,
    "mirror": false,
    "size": 17,
    "html_url": "https://git.example.com/Test/test",
    "ssh_url": "ssh://git@git.example.com/Test/test.git",
    "clone_url": "https://git.example.com/Test/test.git",
    "original_url": "",
    "website": "",
    "stars_count": 0,
    "forks_count": 0,
    "watchers_count": 1,
    "open_issues_count": 0,
    "open_pr_counter": 0,
    "release_counter": 0,
    "default_branch": "master",
    "archived": false,
    "created_at": "2019-03-03T17:26:23Z",
    "updated_at": "2021-03-09T20:12:20Z",
    "permissions": {
      "admin": true,
      "push": true,
      "pull": true
    },
    "has_issues": true,
    "internal_tracker": {
      "enable_time_tracker": false,
      "allow_only_contributors_to_track_time": true,
      "enable_issue_dependencies": true
    },
    "has_wiki": true,
    "has_pull_requests": true,
    "has_projects": false,
    "ignore_whitespace_conflicts": false,
    "allow_merge_commits": true,
    "allow_rebase": true,
    "allow_rebase_explicit": true,
    "allow_squash_merge": true,
    "avatar_url": "",
    "internal": false
  },
  "pusher": {
    "id": 1,
    "login": "Test",
    "full_name": "Test User",
    "email": "Test@example.com",
    "avatar_url": "https://git.example.com/user/avatar/Test/-1",
    "language": "en-US",
    "is_admin": true,
    "last_login": "2021-03-09T20:10:52Z",
    "created": "2018-06-05T09:41:06Z",
    "username": "Test"
  },
  "sender": {
    "id": 1,
    "login": "Test",
    "full_name": "Test User",
    "email": "Test@example.com",
    "avatar_url": "https://git.example.com/user/avatar/Test/-1",
    "language": "en-US",
    "is_admin": true,
    "last_login": "2021-03-09T20:10:52Z",
    "created": "2018-06-05T09:41:06Z",
    "username": "Test"
  }
}
"""

giteaInvalidSecretPush = rb"""
{
  "secret": "invalidSecret",
  "ref": "refs/heads/feature-branch",
  "before": "0000000000000000000000000000000000000000",
  "after": "9d7157cc4a137b3e1dfe92750ccfb1bbad239f99",
  "compare_url": "https://git.example.com/",
  "commits": [
    {
      "id": "9d7157cc4a137b3e1dfe92750ccfb1bbad239f99",
      "message": "TestBranch\n",
      "url": "https://git.example.com/max/webhook_test/commit/9d7157cc4a137b3e1dfe92750ccfb1bbad239f99",
      "author": {
        "name": "Max Mustermann",
        "email": "max@example.com",
        "username": "max"
      },
      "committer": {
        "name": "Max Mustermann",
        "email": "max@example.com",
        "username": "max"
      },
      "verification": null,
      "timestamp": "2018-09-04T12:10:14Z"
    }
  ],
  "repository": {
    "id": 20,
    "owner": {
      "id": 1,
      "login": "max",
      "full_name": "Max Mustermann",
      "email": "max@example.com",
      "avatar_url": "https://secure.gravatar.com/avatar/c9a5fca94b7fd6f8d4dbab8d1575e4fc?d=identicon",
      "language": "en-US",
      "username": "max"
    },
    "name": "webhook_test",
    "full_name": "max/webhook_test",
    "description": "",
    "empty": false,
    "private": true,
    "fork": false,
    "parent": null,
    "mirror": false,
    "size": 48,
    "html_url": "https://git.example.com/max/webhook_test",
    "ssh_url": "ssh://git@git.example.com/max/webhook_test.git",
    "clone_url": "https://git.example.com/max/webhook_test.git",
    "website": "",
    "stars_count": 0,
    "forks_count": 0,
    "watchers_count": 1,
    "open_issues_count": 0,
    "default_branch": "master",
    "created_at": "2018-09-04T10:45:23Z",
    "updated_at": "2018-09-04T12:10:14Z",
    "permissions": {
      "admin": false,
      "push": false,
      "pull": false
    }
  },
  "pusher": {
    "id": 1,
    "login": "max",
    "full_name": "Max Mustermann",
    "email": "max@example.com",
    "avatar_url": "https://secure.gravatar.com/avatar/c9a5fca94b7fd6f8d4dbab8d1575e4fc?d=identicon",
    "language": "en-US",
    "username": "max"
  },
  "sender": {
    "id": 1,
    "login": "max",
    "full_name": "Max Mustermann",
    "email": "max@example.com",
    "avatar_url": "https://secure.gravatar.com/avatar/c9a5fca94b7fd6f8d4dbab8d1575e4fc?d=identicon",
    "language": "en-US",
    "username": "max"
  }
}
"""

giteaJsonPullRequestPayload = rb"""
{
  "secret": "test",
  "action": "opened",
  "number": 1,
  "pull_request": {
    "id": 8,
    "url": "",
    "number": 1,
    "user": {
      "id": 1,
      "login": "max",
      "full_name": "Max Mustermann",
      "email": "max@example.com",
      "avatar_url": "https://secure.gravatar.com/avatar/c9a5fca94b7fd6f8d4dbab8d1575e4fc?d=identicon",
      "language": "en-US",
      "username": "max"
    },
    "title": "TestPR",
    "body": "",
    "labels": [],
    "milestone": null,
    "assignee": null,
    "assignees": null,
    "state": "open",
    "comments": 0,
    "html_url": "https://git.example.com/max/webhook_test/pulls/1",
    "diff_url": "https://git.example.com/max/webhook_test/pulls/1.diff",
    "patch_url": "https://git.example.com/max/webhook_test/pulls/1.patch",
    "mergeable": true,
    "merged": false,
    "merged_at": null,
    "merge_commit_sha": null,
    "merged_by": null,
    "base": {
      "label": "master",
      "ref": "master",
      "sha": "7c5de0796c409e7802abe759113d7fc37e0d6578",
      "repo_id": 20,
      "repo": {
        "id": 20,
        "owner": {
          "id": 1,
          "login": "max",
          "full_name": "Max Mustermann",
          "email": "max@example.com",
          "avatar_url": "https://secure.gravatar.com/avatar/c9a5fca94b7fd6f8d4dbab8d1575e4fc?d=identicon",
          "language": "en-US",
          "username": "max"
        },
        "name": "webhook_test",
        "full_name": "max/webhook_test",
        "description": "",
        "empty": false,
        "private": true,
        "fork": false,
        "parent": null,
        "mirror": false,
        "size": 48,
        "html_url": "https://git.example.com/max/webhook_test",
        "ssh_url": "ssh://git@git.example.com/max/webhook_test.git",
        "clone_url": "https://git.example.com/max/webhook_test.git",
        "website": "",
        "stars_count": 0,
        "forks_count": 0,
        "watchers_count": 1,
        "open_issues_count": 0,
        "default_branch": "master",
        "created_at": "2018-09-04T10:45:23Z",
        "updated_at": "2018-09-04T12:10:14Z",
        "permissions": {
          "admin": false,
          "push": false,
          "pull": false
        }
      }
    },
    "head": {
      "label": "feature-branch",
      "ref": "feature-branch",
      "sha": "9d7157cc4a137b3e1dfe92750ccfb1bbad239f99",
      "repo_id": 20,
      "repo": {
        "id": 20,
        "owner": {
          "id": 1,
          "login": "max",
          "full_name": "Max Mustermann",
          "email": "max@example.com",
          "avatar_url": "https://secure.gravatar.com/avatar/c9a5fca94b7fd6f8d4dbab8d1575e4fc?d=identicon",
          "language": "en-US",
          "username": "max"
        },
        "name": "webhook_test",
        "full_name": "max/webhook_test",
        "description": "",
        "empty": false,
        "private": true,
        "fork": false,
        "parent": null,
        "mirror": false,
        "size": 48,
        "html_url": "https://git.example.com/max/webhook_test",
        "ssh_url": "ssh://git@git.example.com/max/webhook_test.git",
        "clone_url": "https://git.example.com/max/webhook_test.git",
        "website": "",
        "stars_count": 0,
        "forks_count": 0,
        "watchers_count": 1,
        "open_issues_count": 0,
        "default_branch": "master",
        "created_at": "2018-09-04T10:45:23Z",
        "updated_at": "2018-09-04T12:10:14Z",
        "permissions": {
          "admin": false,
          "push": false,
          "pull": false
        }
      }
    },
    "merge_base": "7c5de0796c409e7802abe759113d7fc37e0d6578",
    "due_date": null,
    "created_at": "2018-09-04T12:14:49Z",
    "updated_at": "2018-09-04T12:14:49Z",
    "closed_at": null
  },
  "repository": {
    "id": 20,
    "owner": {
      "id": 1,
      "login": "max",
      "full_name": "Max Mustermann",
      "email": "max@example.com",
      "avatar_url": "https://secure.gravatar.com/avatar/c9a5fca94b7fd6f8d4dbab8d1575e4fc?d=identicon",
      "language": "en-US",
      "username": "max"
    },
    "name": "webhook_test",
    "full_name": "max/webhook_test",
    "description": "",
    "empty": false,
    "private": true,
    "fork": false,
    "parent": null,
    "mirror": false,
    "size": 48,
    "html_url": "https://git.example.com/max/webhook_test",
    "ssh_url": "ssh://git@git.example.com/max/webhook_test.git",
    "clone_url": "https://git.example.com/max/webhook_test.git",
    "website": "",
    "stars_count": 0,
    "forks_count": 0,
    "watchers_count": 1,
    "open_issues_count": 0,
    "default_branch": "master",
    "created_at": "2018-09-04T10:45:23Z",
    "updated_at": "2018-09-04T12:10:14Z",
    "permissions": {
      "admin": true,
      "push": true,
      "pull": true
    }
  },
  "sender": {
    "id": 1,
    "login": "max",
    "full_name": "Max Mustermann",
    "email": "max@example.com",
    "avatar_url": "https://secure.gravatar.com/avatar/c9a5fca94b7fd6f8d4dbab8d1575e4fc?d=identicon",
    "language": "en-US",
    "username": "max"
  }
}
"""

giteaJsonPullRequestPayloadNotMergeable = rb"""
{
  "secret": "test",
  "action": "opened",
  "number": 1,
  "pull_request": {
    "id": 8,
    "url": "",
    "number": 1,
    "user": {
      "id": 1,
      "login": "max",
      "full_name": "Max Mustermann",
      "email": "max@example.com",
      "avatar_url": "https://secure.gravatar.com/avatar/c9a5fca94b7fd6f8d4dbab8d1575e4fc?d=identicon",
      "language": "en-US",
      "username": "max"
    },
    "title": "TestPR",
    "body": "",
    "labels": [],
    "milestone": null,
    "assignee": null,
    "assignees": null,
    "state": "open",
    "comments": 0,
    "html_url": "https://git.example.com/max/webhook_test/pulls/1",
    "diff_url": "https://git.example.com/max/webhook_test/pulls/1.diff",
    "patch_url": "https://git.example.com/max/webhook_test/pulls/1.patch",
    "mergeable": false,
    "merged": false,
    "merged_at": null,
    "merge_commit_sha": null,
    "merged_by": null,
    "base": {
      "label": "master",
      "ref": "master",
      "sha": "7c5de0796c409e7802abe759113d7fc37e0d6578",
      "repo_id": 20,
      "repo": {
        "id": 20,
        "owner": {
          "id": 1,
          "login": "max",
          "full_name": "Max Mustermann",
          "email": "max@example.com",
          "avatar_url": "https://secure.gravatar.com/avatar/c9a5fca94b7fd6f8d4dbab8d1575e4fc?d=identicon",
          "language": "en-US",
          "username": "max"
        },
        "name": "webhook_test",
        "full_name": "max/webhook_test",
        "description": "",
        "empty": false,
        "private": true,
        "fork": false,
        "parent": null,
        "mirror": false,
        "size": 48,
        "html_url": "https://git.example.com/max/webhook_test",
        "ssh_url": "ssh://git@git.example.com/max/webhook_test.git",
        "clone_url": "https://git.example.com/max/webhook_test.git",
        "website": "",
        "stars_count": 0,
        "forks_count": 0,
        "watchers_count": 1,
        "open_issues_count": 0,
        "default_branch": "master",
        "created_at": "2018-09-04T10:45:23Z",
        "updated_at": "2018-09-04T12:10:14Z",
        "permissions": {
          "admin": false,
          "push": false,
          "pull": false
        }
      }
    },
    "head": {
      "label": "feature-branch",
      "ref": "feature-branch",
      "sha": "9d7157cc4a137b3e1dfe92750ccfb1bbad239f99",
      "repo_id": 20,
      "repo": {
        "id": 20,
        "owner": {
          "id": 1,
          "login": "max",
          "full_name": "Max Mustermann",
          "email": "max@example.com",
          "avatar_url": "https://secure.gravatar.com/avatar/c9a5fca94b7fd6f8d4dbab8d1575e4fc?d=identicon",
          "language": "en-US",
          "username": "max"
        },
        "name": "webhook_test",
        "full_name": "max/webhook_test",
        "description": "",
        "empty": false,
        "private": true,
        "fork": false,
        "parent": null,
        "mirror": false,
        "size": 48,
        "html_url": "https://git.example.com/max/webhook_test",
        "ssh_url": "ssh://git@git.example.com/max/webhook_test.git",
        "clone_url": "https://git.example.com/max/webhook_test.git",
        "website": "",
        "stars_count": 0,
        "forks_count": 0,
        "watchers_count": 1,
        "open_issues_count": 0,
        "default_branch": "master",
        "created_at": "2018-09-04T10:45:23Z",
        "updated_at": "2018-09-04T12:10:14Z",
        "permissions": {
          "admin": false,
          "push": false,
          "pull": false
        }
      }
    },
    "merge_base": "7c5de0796c409e7802abe759113d7fc37e0d6578",
    "due_date": null,
    "created_at": "2018-09-04T12:14:49Z",
    "updated_at": "2018-09-04T12:14:49Z",
    "closed_at": null
  },
  "repository": {
    "id": 20,
    "owner": {
      "id": 1,
      "login": "max",
      "full_name": "Max Mustermann",
      "email": "max@example.com",
      "avatar_url": "https://secure.gravatar.com/avatar/c9a5fca94b7fd6f8d4dbab8d1575e4fc?d=identicon",
      "language": "en-US",
      "username": "max"
    },
    "name": "webhook_test",
    "full_name": "max/webhook_test",
    "description": "",
    "empty": false,
    "private": true,
    "fork": false,
    "parent": null,
    "mirror": false,
    "size": 48,
    "html_url": "https://git.example.com/max/webhook_test",
    "ssh_url": "ssh://git@git.example.com/max/webhook_test.git",
    "clone_url": "https://git.example.com/max/webhook_test.git",
    "website": "",
    "stars_count": 0,
    "forks_count": 0,
    "watchers_count": 1,
    "open_issues_count": 0,
    "default_branch": "master",
    "created_at": "2018-09-04T10:45:23Z",
    "updated_at": "2018-09-04T12:10:14Z",
    "permissions": {
      "admin": true,
      "push": true,
      "pull": true
    }
  },
  "sender": {
    "id": 1,
    "login": "max",
    "full_name": "Max Mustermann",
    "email": "max@example.com",
    "avatar_url": "https://secure.gravatar.com/avatar/c9a5fca94b7fd6f8d4dbab8d1575e4fc?d=identicon",
    "language": "en-US",
    "username": "max"
  }
}
"""

giteaJsonPullRequestPayloadMerged = rb"""
{
  "secret": "test",
  "action": "opened",
  "number": 1,
  "pull_request": {
    "id": 8,
    "url": "",
    "number": 1,
    "user": {
      "id": 1,
      "login": "max",
      "full_name": "Max Mustermann",
      "email": "max@example.com",
      "avatar_url": "https://secure.gravatar.com/avatar/c9a5fca94b7fd6f8d4dbab8d1575e4fc?d=identicon",
      "language": "en-US",
      "username": "max"
    },
    "title": "TestPR",
    "body": "",
    "labels": [],
    "milestone": null,
    "assignee": null,
    "assignees": null,
    "state": "open",
    "comments": 0,
    "html_url": "https://git.example.com/max/webhook_test/pulls/1",
    "diff_url": "https://git.example.com/max/webhook_test/pulls/1.diff",
    "patch_url": "https://git.example.com/max/webhook_test/pulls/1.patch",
    "mergeable": true,
    "merged": true,
    "merged_at": null,
    "merge_commit_sha": null,
    "merged_by": null,
    "base": {
      "label": "master",
      "ref": "master",
      "sha": "7c5de0796c409e7802abe759113d7fc37e0d6578",
      "repo_id": 20,
      "repo": {
        "id": 20,
        "owner": {
          "id": 1,
          "login": "max",
          "full_name": "Max Mustermann",
          "email": "max@example.com",
          "avatar_url": "https://secure.gravatar.com/avatar/c9a5fca94b7fd6f8d4dbab8d1575e4fc?d=identicon",
          "language": "en-US",
          "username": "max"
        },
        "name": "webhook_test",
        "full_name": "max/webhook_test",
        "description": "",
        "empty": false,
        "private": true,
        "fork": false,
        "parent": null,
        "mirror": false,
        "size": 48,
        "html_url": "https://git.example.com/max/webhook_test",
        "ssh_url": "ssh://git@git.example.com/max/webhook_test.git",
        "clone_url": "https://git.example.com/max/webhook_test.git",
        "website": "",
        "stars_count": 0,
        "forks_count": 0,
        "watchers_count": 1,
        "open_issues_count": 0,
        "default_branch": "master",
        "created_at": "2018-09-04T10:45:23Z",
        "updated_at": "2018-09-04T12:10:14Z",
        "permissions": {
          "admin": false,
          "push": false,
          "pull": false
        }
      }
    },
    "head": {
      "label": "feature-branch",
      "ref": "feature-branch",
      "sha": "9d7157cc4a137b3e1dfe92750ccfb1bbad239f99",
      "repo_id": 20,
      "repo": {
        "id": 20,
        "owner": {
          "id": 1,
          "login": "max",
          "full_name": "Max Mustermann",
          "email": "max@example.com",
          "avatar_url": "https://secure.gravatar.com/avatar/c9a5fca94b7fd6f8d4dbab8d1575e4fc?d=identicon",
          "language": "en-US",
          "username": "max"
        },
        "name": "webhook_test",
        "full_name": "max/webhook_test",
        "description": "",
        "empty": false,
        "private": true,
        "fork": false,
        "parent": null,
        "mirror": false,
        "size": 48,
        "html_url": "https://git.example.com/max/webhook_test",
        "ssh_url": "ssh://git@git.example.com/max/webhook_test.git",
        "clone_url": "https://git.example.com/max/webhook_test.git",
        "website": "",
        "stars_count": 0,
        "forks_count": 0,
        "watchers_count": 1,
        "open_issues_count": 0,
        "default_branch": "master",
        "created_at": "2018-09-04T10:45:23Z",
        "updated_at": "2018-09-04T12:10:14Z",
        "permissions": {
          "admin": false,
          "push": false,
          "pull": false
        }
      }
    },
    "merge_base": "7c5de0796c409e7802abe759113d7fc37e0d6578",
    "due_date": null,
    "created_at": "2018-09-04T12:14:49Z",
    "updated_at": "2018-09-04T12:14:49Z",
    "closed_at": null
  },
  "repository": {
    "id": 20,
    "owner": {
      "id": 1,
      "login": "max",
      "full_name": "Max Mustermann",
      "email": "max@example.com",
      "avatar_url": "https://secure.gravatar.com/avatar/c9a5fca94b7fd6f8d4dbab8d1575e4fc?d=identicon",
      "language": "en-US",
      "username": "max"
    },
    "name": "webhook_test",
    "full_name": "max/webhook_test",
    "description": "",
    "empty": false,
    "private": true,
    "fork": false,
    "parent": null,
    "mirror": false,
    "size": 48,
    "html_url": "https://git.example.com/max/webhook_test",
    "ssh_url": "ssh://git@git.example.com/max/webhook_test.git",
    "clone_url": "https://git.example.com/max/webhook_test.git",
    "website": "",
    "stars_count": 0,
    "forks_count": 0,
    "watchers_count": 1,
    "open_issues_count": 0,
    "default_branch": "master",
    "created_at": "2018-09-04T10:45:23Z",
    "updated_at": "2018-09-04T12:10:14Z",
    "permissions": {
      "admin": true,
      "push": true,
      "pull": true
    }
  },
  "sender": {
    "id": 1,
    "login": "max",
    "full_name": "Max Mustermann",
    "email": "max@example.com",
    "avatar_url": "https://secure.gravatar.com/avatar/c9a5fca94b7fd6f8d4dbab8d1575e4fc?d=identicon",
    "language": "en-US",
    "username": "max"
  }
}
"""


class TestChangeHookGiteaPush(unittest.TestCase, TestReactorMixin):
    def setUp(self):
        self.setUpTestReactor()
        self.changeHook = change_hook.ChangeHookResource(
            dialects={'gitea': {}},
            master=fakeMasterForHooks(self))

    def checkChangesFromPush(self, codebase=None):
        self.assertEqual(len(self.changeHook.master.data.updates.changesAdded), 2)
        change = self.changeHook.master.data.updates.changesAdded[0]
        self.assertEqual(change['repository'], 'ssh://git@git.example.com/max/webhook_test.git')

        self.assertEqual(
            change["author"], "Max Mustermann <max@example.com>")
        self.assertEqual(
            change["revision"], 'ad7157cc4a137b3e1dfe92750ccfb1bbad239f9a')
        self.assertEqual(
            change["when_timestamp"],
            1536063014)
        self.assertEqual(
            change["comments"], "TestBranch2\n")
        self.assertEqual(change["branch"], "feature-branch")
        self.assertEqual(change[
            "revlink"],
            "https://git.example.com/max/webhook_test/commit/ad7157cc4a137b3e1dfe92750ccfb1bbad239f9a")
        change = self.changeHook.master.data.updates.changesAdded[1]

        self.assertEqual(change['repository'], 'ssh://git@git.example.com/max/webhook_test.git')

        self.assertEqual(
            change["author"], "Max Mustermann <max@example.com>")
        self.assertEqual(
            change["revision"], '9d7157cc4a137b3e1dfe92750ccfb1bbad239f99')
        self.assertEqual(
            change["when_timestamp"],
            1536063014)
        self.assertEqual(
            change["comments"], "TestBranch\n")
        self.assertEqual(change["branch"], "feature-branch")
        self.assertEqual(change[
            "revlink"],
            "https://git.example.com/max/webhook_test/commit/9d7157cc4a137b3e1dfe92750ccfb1bbad239f99")

    def checkFileChanges(self, codebase=None):
        self.assertEqual(len(self.changeHook.master.data.updates.changesAdded), 1)
        change = self.changeHook.master.data.updates.changesAdded[0]
        self.assertEqual(change['repository'], 'ssh://git@git.example.com/Test/test.git')

        self.assertEqual(
            change["author"], "Test User <Test@example.com>")
        self.assertEqual(
            change["revision"], 'ea07c3148db428876add8b312256239275c395fb')
        self.assertEqual(
            change["comments"], "test123\n")
        self.assertEqual(change["branch"], "master")
        self.assertEqual(change[
            "revlink"],
            "https://git.example.com/Test/test/commit/ea07c3148db428876add8b312256239275c395fb")
        self.assertEqual(change["files"], ["testfile2", "testfile1", "testfile3"])

    def checkChangesFromPullRequest(self, codebase=None):
        self.assertEqual(len(self.changeHook.master.data.updates.changesAdded), 1)
        change = self.changeHook.master.data.updates.changesAdded[0]
        self.assertEqual(change['repository'], 'ssh://git@git.example.com/max/webhook_test.git')

        self.assertEqual(
            change["author"], "Max Mustermann <max@example.com>")
        self.assertEqual(
            change["revision"], '9d7157cc4a137b3e1dfe92750ccfb1bbad239f99')
        self.assertEqual(
            change["when_timestamp"],
            1536063289)
        self.assertEqual(
            change["comments"], "PR#1: TestPR\n\n")
        self.assertEqual(change["branch"], "feature-branch")
        self.assertEqual(change[
            "revlink"], "https://git.example.com/max/webhook_test/pulls/1")
        properties = change["properties"]
        self.assertEqual(properties["base_branch"], "master")
        self.assertEqual(properties["base_sha"], "7c5de0796c409e7802abe759113d7fc37e0d6578")
        self.assertEqual(properties["base_repository"], "https://git.example.com/max/webhook_test.git")
        self.assertEqual(properties["base_git_ssh_url"], "ssh://git@git.example.com/max/webhook_test.git")

        self.assertEqual(properties["head_branch"], "feature-branch")
        self.assertEqual(properties["head_sha"], "9d7157cc4a137b3e1dfe92750ccfb1bbad239f99")
        self.assertEqual(properties["head_repository"], "https://git.example.com/max/webhook_test.git")
        self.assertEqual(properties["head_git_ssh_url"], "ssh://git@git.example.com/max/webhook_test.git")

        self.assertEqual(properties["pr_id"], 8)
        self.assertEqual(properties["pr_number"], 1)

    @defer.inlineCallbacks
    def testPushEvent(self):
        self.request = FakeRequest(content=giteaJsonPushPayload)
        self.request.uri = b'/change_hook/gitea'
        self.request.method = b'POST'
        self.request.received_headers[_HEADER_EVENT_TYPE] = b"push"
        res = yield self.request.test_render(self.changeHook)
        self.checkChangesFromPush(res)

    @defer.inlineCallbacks
    def testChangedFiles(self):
        self.request = FakeRequest(content=giteaJsonPushModifiedFiles)
        self.request.uri = b'/change_hook/gitea'
        self.request.method = b'POST'
        self.request.received_headers[_HEADER_EVENT_TYPE] = b"push"
        res = yield self.request.test_render(self.changeHook)
        self.checkFileChanges(res)

    @defer.inlineCallbacks
    def testPullRequestEvent(self):
        self.request = FakeRequest(content=giteaJsonPullRequestPayload)
        self.request.uri = b'/change_hook/gitea'
        self.request.method = b'POST'
        self.request.received_headers[_HEADER_EVENT_TYPE] = b"pull_request"
        res = yield self.request.test_render(self.changeHook)
        self.checkChangesFromPullRequest(res)

    @defer.inlineCallbacks
    def testPullRequestNotMergeableEvent(self):
        self.request = FakeRequest(content=giteaJsonPullRequestPayloadNotMergeable)
        self.request.uri = b'/change_hook/gitea'
        self.request.method = b'POST'
        self.request.received_headers[_HEADER_EVENT_TYPE] = b"pull_request"
        yield self.request.test_render(self.changeHook)
        self.assertEqual(len(self.changeHook.master.data.updates.changesAdded), 0)

    @defer.inlineCallbacks
    def testPullRequestMergedEvent(self):
        self.request = FakeRequest(content=giteaJsonPullRequestPayloadMerged)
        self.request.uri = b'/change_hook/gitea'
        self.request.method = b'POST'
        self.request.received_headers[_HEADER_EVENT_TYPE] = b"pull_request"
        yield self.request.test_render(self.changeHook)
        self.assertEqual(len(self.changeHook.master.data.updates.changesAdded), 0)


class TestChangeHookGiteaPushOnlySingle(unittest.TestCase, TestReactorMixin):
    def setUp(self):
        self.setUpTestReactor()
        self.changeHook = change_hook.ChangeHookResource(
            dialects={'gitea': {"onlyIncludePushCommit": True}},
            master=fakeMasterForHooks(self))

    def checkChangesFromPush(self, codebase=None):
        self.assertEqual(len(self.changeHook.master.data.updates.changesAdded), 1)
        change = self.changeHook.master.data.updates.changesAdded[0]
        self.assertEqual(change['repository'], 'ssh://git@git.example.com/max/webhook_test.git')

        self.assertEqual(
            change["author"], "Max Mustermann <max@example.com>")
        self.assertEqual(
            change["revision"], '9d7157cc4a137b3e1dfe92750ccfb1bbad239f99')
        self.assertEqual(
            change["when_timestamp"],
            1536063014)
        self.assertEqual(
            change["comments"], "TestBranch\n")
        self.assertEqual(change["branch"], "feature-branch")
        self.assertEqual(change[
            "revlink"],
            "https://git.example.com/max/webhook_test/commit/9d7157cc4a137b3e1dfe92750ccfb1bbad239f99")

    @defer.inlineCallbacks
    def testPushEvent(self):
        self.request = FakeRequest(content=giteaJsonPushPayload)
        self.request.uri = b'/change_hook/gitea'
        self.request.method = b'POST'
        self.request.received_headers[_HEADER_EVENT_TYPE] = b"push"
        res = yield self.request.test_render(self.changeHook)
        self.checkChangesFromPush(res)


class TestChangeHookGiteaSecretPhrase(unittest.TestCase, TestReactorMixin):
    def setUp(self):
        self.setUpTestReactor()
        self.changeHook = change_hook.ChangeHookResource(
            dialects={'gitea': {"secret": "test"}},
            master=fakeMasterForHooks(self))

    @defer.inlineCallbacks
    def testValidSecret(self):
        self.request = FakeRequest(content=giteaJsonPushPayload)
        self.request.uri = b'/change_hook/gitea'
        self.request.method = b'POST'
        self.request.received_headers[_HEADER_EVENT_TYPE] = b"push"
        yield self.request.test_render(self.changeHook)
        self.assertEqual(len(self.changeHook.master.data.updates.changesAdded), 2)

    @defer.inlineCallbacks
    def testInvalidSecret(self):
        self.request = FakeRequest(content=giteaInvalidSecretPush)
        self.request.uri = b'/change_hook/gitea'
        self.request.method = b'POST'
        self.request.received_headers[_HEADER_EVENT_TYPE] = b"push"
        yield self.request.test_render(self.changeHook)
        self.assertEqual(len(self.changeHook.master.data.updates.changesAdded), 0)

class TestChangeHookGiteaClass(unittest.TestCase, TestReactorMixin):
    class GiteaTestHandler(GiteaHandler):
        fakeCategory = 'definitely-not-a-real-category'

        def process_push(self, _, __, ___):
            return [{'category': self.fakeCategory}]

        def process_release(self, _, __, ___):
            return [{'category': self.fakeCategory}]

    def setUp(self):
        self.setUpTestReactor()
        self.changeHook = change_hook.ChangeHookResource(
            dialects={'gitea': {'class': self.GiteaTestHandler}},
            master=fakeMasterForHooks(self))

    def checkChanges(self):
        # There should only be one change because our fake handlers throw the
        # payloads away and returns their own single change with a single field.
        self.assertEqual(len(self.changeHook.master.data.updates.changesAdded), 1)
        change = self.changeHook.master.data.updates.changesAdded[0]
        self.assertEqual(change['category'], self.GiteaTestHandler.fakeCategory)        

    @defer.inlineCallbacks
    def testOverrideHandlerIsUsed(self):
        self.request = FakeRequest(content=giteaJsonPushPayload)
        self.request.uri = b'/change_hook/gitea'
        self.request.method = b'POST'
        self.request.received_headers[_HEADER_EVENT_TYPE] = b'push'
        yield self.request.test_render(self.changeHook)

        self.checkChanges()

    @defer.inlineCallbacks
    def testNewHandler(self):
        self.request = FakeRequest(content=giteaJsonPushPayload)
        self.request.uri = b'/change_hook/gitea'
        self.request.method = b'POST'
        self.request.received_headers[_HEADER_EVENT_TYPE] = b'release'
        yield self.request.test_render(self.changeHook)

        self.checkChanges()
