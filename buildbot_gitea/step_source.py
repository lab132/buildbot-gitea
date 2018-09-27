

from __future__ import absolute_import
from __future__ import print_function

from twisted.internet import defer
from twisted.python import log

from buildbot.steps.source.git import Git


class Gitea(Git):
    """
    Source step that knows how to handle merge requests from
    the Gitea webhook
    """
    @defer.inlineCallbacks
    def _fetch(self, arg):
        res = yield super(Gitea, self)._fetch(arg)
        if self.build.hasProperty("pr_id"):
            remote = yield self._dovccmd(
                ['config', 'remote.pr_source.url'], collectStdout=True)
            if remote is None or remote.strip() is '':
                yield self._dovccmd(
                    ['remote', 'add', 'pr_source',
                     self.build.getProperty("head_git_ssh_url", None)])
            else:
                yield self._dovccmd(
                    ['remote', 'set-url', 'pr_source',
                     self.build.getProperty("head_git_ssh_url", None)])
            yield self._dovccmd(['fetch', 'pr_source'])
            res = yield self._dovccmd(['merge', self.build.getProperty("head_sha", None)])
        defer.returnValue(res)