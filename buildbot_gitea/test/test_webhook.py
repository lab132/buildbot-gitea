import buildbot.www.change_hook as change_hook
from buildbot.test.fake.web import FakeRequest
from buildbot.test.fake.web import fakeMasterForHooks
from buildbot.test.reactor import TestReactorMixin
from buildbot.secrets.manager import SecretManager
from buildbot.test.fake.secrets import FakeSecretStorage
from buildbot.process.properties import Secret



from twisted.internet import defer
from twisted.trial import unittest

from buildbot_gitea.webhook import GiteaHandler, _HEADER_EVENT_TYPE, _HEADER_SIGNATURE

giteaJsonPushPayload_Signature = 'b5feb0994ad24c209188d36a30cecfea86666aa9c65a419b068f73f91152e7bc'

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

giteaJsonPullRequestPayload_Signature = '8685905c03fa521dd1eacfb84405195dbca2a08206c3a978a3656399f5dbe01a'

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


giteaJsonPullRequestPayloadNotMergeable_Signature = '5552a0cbcbb3fe6286681bc7846754929be0d3f27ccc32914e5fd3ce01f34632'

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

giteaJsonPullRequestPayloadMerged_Signature = '4d3b1045aea9aa5cce4f7270d549c11d212c55036d9c547d0c9327891d56bf97'
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

giteaJsonPullRequestFork = rb"""
{
  "secret": "test",
  "action": "opened",
  "number": 4,
  "pull_request": {
    "id": 36,
    "url": "https://git.example.com/testuser/webhook_test/pulls/4",
    "number": 4,
    "user": {
      "id": 1,
      "login": "testuser",
      "full_name": "testuser name",
      "email": "testuser@example.com",
      "avatar_url": "https://git.example.com/user/avatar/testuser/-1",
      "language": "en-US",
      "is_admin": true,
      "last_login": "2021-03-27T13:53:28Z",
      "created": "2018-06-05T09:41:06Z",
      "username": "testuser"
    },
    "title": "testfork",
    "body": "Test PR",
    "labels": [],
    "milestone": null,
    "assignee": null,
    "assignees": null,
    "state": "open",
    "is_locked": false,
    "comments": 0,
    "html_url": "https://git.example.com/testuser/webhook_test/pulls/4",
    "diff_url": "https://git.example.com/testuser/webhook_test/pulls/4.diff",
    "patch_url": "https://git.example.com/testuser/webhook_test/pulls/4.patch",
    "mergeable": true,
    "merged": false,
    "merged_at": null,
    "merge_commit_sha": null,
    "merged_by": null,
    "base": {
      "label": "master",
      "ref": "master",
      "sha": "449a5a8ca05607106b5ba41988c1a658a8949a18",
      "repo_id": 20,
      "repo": {
        "id": 20,
        "owner": {
          "id": 1,
          "login": "testuser",
          "full_name": "testuser name",
          "email": "testuser@example.com",
          "avatar_url": "https://git.example.com/user/avatar/testuser/-1",
          "language": "en-US",
          "is_admin": true,
          "last_login": "2021-03-27T13:53:28Z",
          "created": "2018-06-05T09:41:06Z",
          "username": "testuser"
        },
        "name": "webhook_test",
        "full_name": "testuser/webhook_test",
        "description": "",
        "empty": false,
        "private": true,
        "fork": false,
        "template": false,
        "parent": null,
        "mirror": false,
        "size": 76,
        "html_url": "https://git.example.com/testuser/webhook_test",
        "ssh_url": "ssh://git@git.example.com/testuser/webhook_test.git",
        "clone_url": "https://git.example.com/testuser/webhook_test.git",
        "original_url": "",
        "website": "",
        "stars_count": 0,
        "forks_count": 1,
        "watchers_count": 1,
        "open_issues_count": 0,
        "open_pr_counter": 1,
        "release_counter": 0,
        "default_branch": "master",
        "archived": false,
        "created_at": "2018-09-04T10:45:23Z",
        "updated_at": "2018-09-04T13:05:51Z",
        "permissions": {
          "admin": false,
          "push": false,
          "pull": false
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
      }
    },
    "head": {
      "label": "feature_branch",
      "ref": "feature_branch",
      "sha": "53e3075cbe468f14c2801d186d703e64b2adee12",
      "repo_id": 34,
      "repo": {
        "id": 34,
        "owner": {
          "id": 14,
          "login": "test_org",
          "full_name": "",
          "email": "",
          "avatar_url": "https://git.example.com/user/avatar/test_org/-1",
          "language": "",
          "is_admin": false,
          "last_login": "1970-01-01T00:00:00Z",
          "created": "2018-09-27T11:35:41Z",
          "username": "test_org"
        },
        "name": "webhook_test_fork",
        "full_name": "test_org/webhook_test_fork",
        "description": "",
        "empty": false,
        "private": true,
        "fork": true,
        "template": false,
        "parent": {
          "id": 20,
          "owner": {
            "id": 1,
            "login": "testuser",
            "full_name": "testuser name",
            "email": "testuser@example.com",
            "avatar_url": "https://git.example.com/user/avatar/testuser/-1",
            "language": "en-US",
            "is_admin": true,
            "last_login": "2021-03-27T13:53:28Z",
            "created": "2018-06-05T09:41:06Z",
            "username": "testuser"
          },
          "name": "webhook_test",
          "full_name": "testuser/webhook_test",
          "description": "",
          "empty": false,
          "private": true,
          "fork": false,
          "template": false,
          "parent": null,
          "mirror": false,
          "size": 76,
          "html_url": "https://git.example.com/testuser/webhook_test",
          "ssh_url": "ssh://git@git.example.com/testuser/webhook_test.git",
          "clone_url": "https://git.example.com/testuser/webhook_test.git",
          "original_url": "",
          "website": "",
          "stars_count": 0,
          "forks_count": 1,
          "watchers_count": 1,
          "open_issues_count": 0,
          "open_pr_counter": 2,
          "release_counter": 0,
          "default_branch": "master",
          "archived": false,
          "created_at": "2018-09-04T10:45:23Z",
          "updated_at": "2018-09-04T13:05:51Z",
          "permissions": {
            "admin": false,
            "push": false,
            "pull": false
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
        "mirror": false,
        "size": 19,
        "html_url": "https://git.example.com/test_org/webhook_test_fork",
        "ssh_url": "ssh://git@git.example.com/test_org/webhook_test_fork.git",
        "clone_url": "https://git.example.com/test_org/webhook_test_fork.git",
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
        "created_at": "2021-03-28T21:40:46Z",
        "updated_at": "2021-03-28T21:41:01Z",
        "permissions": {
          "admin": false,
          "push": false,
          "pull": false
        },
        "has_issues": true,
        "internal_tracker": {
          "enable_time_tracker": false,
          "allow_only_contributors_to_track_time": true,
          "enable_issue_dependencies": true
        },
        "has_wiki": true,
        "has_pull_requests": true,
        "has_projects": true,
        "ignore_whitespace_conflicts": false,
        "allow_merge_commits": true,
        "allow_rebase": true,
        "allow_rebase_explicit": true,
        "allow_squash_merge": true,
        "avatar_url": "",
        "internal": false
      }
    },
    "merge_base": "449a5a8ca05607106b5ba41988c1a658a8949a18",
    "due_date": null,
    "created_at": "2021-03-28T21:41:24Z",
    "updated_at": "2021-03-28T21:41:24Z",
    "closed_at": null
  },
  "repository": {
    "id": 20,
    "owner": {
      "id": 1,
      "login": "testuser",
      "full_name": "testuser name",
      "email": "testuser@example.com",
      "avatar_url": "https://git.example.com/user/avatar/testuser/-1",
      "language": "en-US",
      "is_admin": true,
      "last_login": "2021-03-27T13:53:28Z",
      "created": "2018-06-05T09:41:06Z",
      "username": "testuser"
    },
    "name": "webhook_test",
    "full_name": "testuser/webhook_test",
    "description": "",
    "empty": false,
    "private": true,
    "fork": false,
    "template": false,
    "parent": null,
    "mirror": false,
    "size": 76,
    "html_url": "https://git.example.com/testuser/webhook_test",
    "ssh_url": "ssh://git@git.example.com/testuser/webhook_test.git",
    "clone_url": "https://git.example.com/testuser/webhook_test.git",
    "original_url": "",
    "website": "",
    "stars_count": 0,
    "forks_count": 1,
    "watchers_count": 1,
    "open_issues_count": 0,
    "open_pr_counter": 2,
    "release_counter": 0,
    "default_branch": "master",
    "archived": false,
    "created_at": "2018-09-04T10:45:23Z",
    "updated_at": "2018-09-04T13:05:51Z",
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
  "sender": {
    "id": 1,
    "login": "testuser",
    "full_name": "testuser name",
    "email": "testuser@example.com",
    "avatar_url": "https://git.example.com/user/avatar/testuser/-1",
    "language": "en-US",
    "is_admin": true,
    "last_login": "2021-03-27T13:53:28Z",
    "created": "2018-06-05T09:41:06Z",
    "username": "testuser"
  },
  "review": null
}
"""


giteaJsonPushEmptyFiles = rb"""
{
  "secret": "pass",
  "ref": "refs/heads/develop",
  "before": "2437bd7c6b0af7b8da570973c02f0cca07ec787d",
  "after": "2437bd7c6b0af7b8da570973c02f0cca07ec787d",
  "compare_url": "",
  "commits": [
    {
      "id": "2437bd7c6b0af7b8da570973c02f0cca07ec787d",
      "message": "snip",
      "url": "snip/commit/2437bd7c6b0af7b8da570973c02f0cca07ec787d",
      "author": {
        "name": "snip",
        "email": "snip",
        "username": ""
      },
      "committer": {
        "name": "snip",
        "email": "snip",
        "username": ""
      },
      "verification": null,
      "timestamp": "0001-01-01T00:00:00Z",
      "added": null,
      "removed": null,
      "modified": null
    }
  ],
  "head_commit": {
    "id": "2437bd7c6b0af7b8da570973c02f0cca07ec787d",
    "message": "snip",
    "url": "snip/commit/2437bd7c6b0af7b8da570973c02f0cca07ec787d",
    "author": {
      "name": "snip",
      "email": "snip",
      "username": ""
    },
    "committer": {
      "name": "snip",
      "email": "snip",
      "username": ""
    },
    "verification": null,
    "timestamp": "0001-01-01T00:00:00Z",
    "added": null,
    "removed": null,
    "modified": null
  },
  "repository": {
    "id": "snip",
    "owner": {"id":"snip","login":"snip","full_name":"snip","email":"snip","avatar_url":"snip","language":"","is_admin":false,"last_login":"0001-01-01T00:00:00Z","created":"2019-07-04T02:15:26+02:00","restricted":false,"active":false,"prohibit_login":false,"location":"","website":"","description":"","visibility":"public","followers_count":0,"following_count":0,"starred_repos_count":0,"username":"snip"},
    "name": "snip",
    "full_name": "snip",
    "description": "snip",
    "empty": false,
    "private": true,
    "fork": false,
    "template": false,
    "parent": null,
    "mirror": false,
    "size": 19106,
    "html_url": "snip",
    "ssh_url": "git@snip.git",
    "clone_url": "snip.git",
    "original_url": "",
    "website": "",
    "stars_count": 0,
    "forks_count": 0,
    "watchers_count": 5,
    "open_issues_count": 33,
    "open_pr_counter": 1,
    "release_counter": 0,
    "default_branch": "develop",
    "archived": false,
    "created_at": "2020-08-25T09:34:29+02:00",
    "updated_at": "2022-01-19T15:55:11+01:00",
    "permissions": {
      "admin": false,
      "push": false,
      "pull": false
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
    "allow_rebase_explicit": false,
    "allow_squash_merge": true,
    "default_merge_style": "merge",
    "avatar_url": "",
    "internal": false,
    "mirror_interval": ""
  },
  "pusher": {"id":"snip","login":"snip","full_name":"snip","email":"snip","avatar_url":"snip","language":"","is_admin":false,"last_login":"0001-01-01T00:00:00Z","created":"2021-01-22T02:15:29+01:00","restricted":false,"active":false,"prohibit_login":false,"location":"","website":"","description":"","visibility":"public","followers_count":0,"following_count":0,"starred_repos_count":0,"username":"snip"},
  "sender": {"id":"snip","login":"snip","full_name":"snip","email":"snip","avatar_url":"snip","language":"","is_admin":false,"last_login":"0001-01-01T00:00:00Z","created":"2021-01-22T02:15:29+01:00","restricted":false,"active":false,"prohibit_login":false,"location":"","website":"","description":"","visibility":"public","followers_count":0,"following_count":0,"starred_repos_count":0,"username":"snip"}
}
"""

class TestChangeHookGiteaPush(unittest.TestCase, TestReactorMixin):
    def setUp(self):
        self.setup_test_reactor()
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

    def checkNoFileChanges(self, codebase=None):
        self.assertEqual(len(self.changeHook.master.data.updates.changesAdded), 1)
        change = self.changeHook.master.data.updates.changesAdded[0]
        self.assertEqual(change['repository'], 'git@snip.git')

        self.assertEqual(
            change["author"], "snip <snip>")
        self.assertEqual(
            change["revision"], '2437bd7c6b0af7b8da570973c02f0cca07ec787d')
        self.assertEqual(
            change["comments"], "snip")
        self.assertEqual(change["branch"], "develop")
        self.assertEqual(change[
            "revlink"],
            "snip/commit/2437bd7c6b0af7b8da570973c02f0cca07ec787d")
        self.assertEqual(change["files"], [])

    def checkChangesFromPullRequest(self, codebase=None):
        self.assertEqual(len(self.changeHook.master.data.updates.changesAdded), 1)
        change = self.changeHook.master.data.updates.changesAdded[0]
        self.assertEqual(change['repository'], 'ssh://git@git.example.com/max/webhook_test.git')

        self.assertEqual(
            change["author"], "Max Mustermann <max@example.com>")
        self.assertEqual(
            change["revision"], '7c5de0796c409e7802abe759113d7fc37e0d6578')
        self.assertEqual(
            change["when_timestamp"],
            1536063289)
        self.assertEqual(
            change["comments"], "PR#1: TestPR\n\n")
        self.assertEqual(change["branch"], "master")
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

    def checkChangesFromPullRequestFork(self, codebase=None):
        self.assertEqual(len(self.changeHook.master.data.updates.changesAdded), 1)
        change = self.changeHook.master.data.updates.changesAdded[0]
        self.assertEqual(change['repository'], 'ssh://git@git.example.com/testuser/webhook_test.git')

        self.assertEqual(
            change["author"], "testuser name <testuser@example.com>")
        self.assertEqual(
            change["revision"], '449a5a8ca05607106b5ba41988c1a658a8949a18')
        self.assertEqual(change["branch"], "master")
        self.assertEqual(change[
            "revlink"], "https://git.example.com/testuser/webhook_test/pulls/4")
        properties = change["properties"]
        self.assertEqual(properties["base_branch"], "master")
        self.assertEqual(properties["base_sha"], "449a5a8ca05607106b5ba41988c1a658a8949a18")
        self.assertEqual(properties["base_repository"], "https://git.example.com/testuser/webhook_test.git")
        self.assertEqual(properties["base_git_ssh_url"], "ssh://git@git.example.com/testuser/webhook_test.git")

        self.assertEqual(properties["head_branch"], "feature_branch")
        self.assertEqual(properties["head_sha"], "53e3075cbe468f14c2801d186d703e64b2adee12")
        self.assertEqual(properties["head_repository"], "https://git.example.com/test_org/webhook_test_fork.git")
        self.assertEqual(properties["head_git_ssh_url"], "ssh://git@git.example.com/test_org/webhook_test_fork.git")

        self.assertEqual(properties["pr_id"], 36)
        self.assertEqual(properties["pr_number"], 4)

    @defer.inlineCallbacks
    def testPushEvent(self):
        self.request = FakeRequest(content=giteaJsonPushPayload)
        self.request.uri = b'/change_hook/gitea'
        self.request.method = b'POST'
        self.request.received_headers[_HEADER_EVENT_TYPE] = b"push"
        self.request.received_headers[_HEADER_SIGNATURE] = giteaJsonPushPayload_Signature
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
    def testNoChangedFiles(self):
        self.request = FakeRequest(content=giteaJsonPushEmptyFiles)
        self.request.uri = b'/change_hook/gitea'
        self.request.method = b'POST'
        self.request.received_headers[_HEADER_EVENT_TYPE] = b"push"
        res = yield self.request.test_render(self.changeHook)
        self.checkNoFileChanges(res)

    @defer.inlineCallbacks
    def testPullRequestEvent(self):
        self.request = FakeRequest(content=giteaJsonPullRequestPayload)
        self.request.uri = b'/change_hook/gitea'
        self.request.method = b'POST'
        self.request.received_headers[_HEADER_EVENT_TYPE] = b"pull_request"
        self.request.received_headers[_HEADER_SIGNATURE] = giteaJsonPullRequestPayload_Signature
        res = yield self.request.test_render(self.changeHook)
        self.checkChangesFromPullRequest(res)

    @defer.inlineCallbacks
    def testPullRequestForkEvent(self):
        self.request = FakeRequest(content=giteaJsonPullRequestFork)
        self.request.uri = b'/change_hook/gitea'
        self.request.method = b'POST'
        self.request.received_headers[_HEADER_EVENT_TYPE] = b"pull_request"
        res = yield self.request.test_render(self.changeHook)
        self.checkChangesFromPullRequestFork(res)

    @defer.inlineCallbacks
    def testPullRequestNotMergeableEvent(self):
        self.request = FakeRequest(content=giteaJsonPullRequestPayloadNotMergeable)
        self.request.uri = b'/change_hook/gitea'
        self.request.method = b'POST'
        self.request.received_headers[_HEADER_EVENT_TYPE] = b"pull_request"
        self.request.received_headers[_HEADER_SIGNATURE] = giteaJsonPullRequestPayloadNotMergeable_Signature
        yield self.request.test_render(self.changeHook)
        self.assertEqual(len(self.changeHook.master.data.updates.changesAdded), 0)

    @defer.inlineCallbacks
    def testPullRequestMergedEvent(self):
        self.request = FakeRequest(content=giteaJsonPullRequestPayloadMerged)
        self.request.uri = b'/change_hook/gitea'
        self.request.method = b'POST'
        self.request.received_headers[_HEADER_EVENT_TYPE] = b"pull_request"
        self.request.received_headers[_HEADER_SIGNATURE] = giteaJsonPullRequestPayloadMerged_Signature
        yield self.request.test_render(self.changeHook)
        self.assertEqual(len(self.changeHook.master.data.updates.changesAdded), 0)


class TestChangeHookGiteaPushOnlySingle(unittest.TestCase, TestReactorMixin):
    def setUp(self):
        self.setup_test_reactor()
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
        self.request.received_headers[_HEADER_SIGNATURE] = giteaJsonPushPayload_Signature
        res = yield self.request.test_render(self.changeHook)
        self.checkChangesFromPush(res)


class TestChangeHookGiteaSecretPhrase(unittest.TestCase, TestReactorMixin):
    def setUp(self):
        self.setup_test_reactor()
        self.changeHook = change_hook.ChangeHookResource(
            dialects={'gitea': {"secret": "test"}},
            master=fakeMasterForHooks(self))

    @defer.inlineCallbacks
    def testValidSecret(self):
        self.request = FakeRequest(content=giteaJsonPushPayload)
        self.request.uri = b'/change_hook/gitea'
        self.request.method = b'POST'
        self.request.received_headers[_HEADER_EVENT_TYPE] = b"push"
        self.request.received_headers[_HEADER_SIGNATURE] = giteaJsonPushPayload_Signature
        yield self.request.test_render(self.changeHook)
        self.assertEqual(len(self.changeHook.master.data.updates.changesAdded), 2)

    @defer.inlineCallbacks
    def testInvalidSecret(self):
        self.request = FakeRequest(content=giteaInvalidSecretPush)
        self.request.uri = b'/change_hook/gitea'
        self.request.method = b'POST'
        self.request.received_headers[_HEADER_EVENT_TYPE] = b"push"
        self.request.received_headers[_HEADER_SIGNATURE] = giteaJsonPushPayload_Signature
        yield self.request.test_render(self.changeHook)
        self.assertEqual(len(self.changeHook.master.data.updates.changesAdded), 0)


class TestChangeHookGiteaSecretPhraseProvider(unittest.TestCase, TestReactorMixin):
    def setUp(self):
        self.setup_test_reactor()
        self.master = fakeMasterForHooks(self)
        self.changeHook = change_hook.ChangeHookResource(
            dialects={'gitea': {"secret": Secret("token")}},
            master=self.master)

        fake_storage_service = FakeSecretStorage()

        secret_service = SecretManager()
        secret_service.services = [fake_storage_service]
        secret_service.setServiceParent(self.master)
        fake_storage_service.reconfigService(secretdict={"token": "test"})

    @defer.inlineCallbacks
    def testValidSecret(self):
        self.request = FakeRequest(content=giteaJsonPushPayload)
        self.request.uri = b'/change_hook/gitea'
        self.request.method = b'POST'
        self.request.received_headers[_HEADER_EVENT_TYPE] = b"push"
        self.request.received_headers[_HEADER_SIGNATURE] = giteaJsonPushPayload_Signature
        yield self.request.test_render(self.changeHook)
        self.assertEqual(len(self.changeHook.master.data.updates.changesAdded), 2)

    @defer.inlineCallbacks
    def testInvalidSecret(self):
        self.request = FakeRequest(content=giteaInvalidSecretPush)
        self.request.uri = b'/change_hook/gitea'
        self.request.method = b'POST'
        self.request.received_headers[_HEADER_EVENT_TYPE] = b"push"
        self.request.received_headers[_HEADER_SIGNATURE] = giteaJsonPushPayload_Signature
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
        self.setup_test_reactor()
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
        self.request.received_headers[_HEADER_SIGNATURE] = giteaJsonPushPayload_Signature
        yield self.request.test_render(self.changeHook)

        self.checkChanges()

    @defer.inlineCallbacks
    def testNewHandler(self):
        self.request = FakeRequest(content=giteaJsonPushPayload)
        self.request.uri = b'/change_hook/gitea'
        self.request.method = b'POST'
        self.request.received_headers[_HEADER_EVENT_TYPE] = b'release'
        self.request.received_headers[_HEADER_SIGNATURE] = giteaJsonPushPayload_Signature
        yield self.request.test_render(self.changeHook)

        self.checkChanges()
