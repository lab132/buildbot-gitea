
import buildbot.www.change_hook as change_hook
from buildbot.test.fake.web import FakeRequest
from buildbot.test.fake.web import fakeMasterForHooks

import mock

from twisted.internet import defer
from twisted.trial import unittest

from gitea.webhook import _HEADER_EVENT_TYPE

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


class TestChangeHookGiteaPush(unittest.TestCase):
    def setUp(self):
        self.changeHook = change_hook.ChangeHookResource(
            dialects={'gitea': True},
            master=fakeMasterForHooks())

    def checkChangesFromPush(self, codebase=None):
        self.assertEqual(len(self.changeHook.master.addedChanges), 1)
        change = self.changeHook.master.addedChanges[0]
        self.assertEqual(change['repository'], 'ssh://git@git.example.com/max/webhook_test.git')

        self.assertEqual(
            change["author"], "Max Mustermann <max@example.com>")
        self.assertEqual(
            change["revision"], '9d7157cc4a137b3e1dfe92750ccfb1bbad239f99')
        self.assertEqual(
            change["comments"], "TestBranch\n")
        self.assertEqual(change["branch"], "feature-branch")
        self.assertEqual(change[
            "revlink"], "https://git.example.com/max/webhook_test/commit/9d7157cc4a137b3e1dfe92750ccfb1bbad239f99")

    @defer.inlineCallbacks
    def testPushEvent(self):
        self.request = FakeRequest(content=giteaJsonPushPayload)
        self.request.uri = b'/change_hook/gitea'
        self.request.method = b'POST'
        self.request.received_headers[_HEADER_EVENT_TYPE] = b"push"
        res = yield self.request.test_render(self.changeHook)
        self.checkChangesFromPush(res)
