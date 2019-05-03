# This file is part of Buildbot.  Buildbot is free software: you can
# redistribute it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, version 2.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51
# Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# Copyright Buildbot Team Members

from __future__ import absolute_import
from __future__ import print_function

from twisted.trial import unittest

from buildbot.process.results import SUCCESS
from buildbot_gitea.step_source import Gitea
from buildbot.test.fake.remotecommand import Expect
from buildbot.test.fake.remotecommand import ExpectShell
from buildbot.test.util import config
from buildbot.test.util import sourcesteps
from buildbot.test.util.misc import TestReactorMixin



class TestGitea(sourcesteps.SourceStepMixin, config.ConfigErrorsMixin, unittest.TestCase, TestReactorMixin):
    stepClass = Gitea

    def setUp(self):
        self.setUpTestReactor()
        self.sourceName = self.stepClass.__name__
        return self.setUpSourceStep()

    def setupStep(self, step, **kwargs):
        step = sourcesteps.SourceStepMixin.setupStep(self, step, **kwargs)
        step.build.properties.setProperty("pr_id", "1", "gitea pr id")
        step.build.properties.setProperty("base_sha", "f6ad368298bd941e934a41f3babc827b2aa95a1d", "gitea source branch")
        step.build.properties.setProperty("base_branch", "master", "gitea source branch")
        step.build.properties.setProperty("base_git_ssh_url",
            "git@gitea.example.com:base/awesome_project.git",
            "gitea source git ssh url")
        step.build.properties.setProperty("head_sha", "e4cd1224c622d46a8199c85c858485723115d2c8", "gitea target sha")
        step.build.properties.setProperty("head_branch", "feature-branch", "gitea target branch")
        step.build.properties.setProperty("head_git_ssh_url",
            "git@gitea.example.com:target/awesome_project.git",
            "gitea target git ssh url")
        return step

    def tearDown(self):
        return self.tearDownSourceStep()

    def test_with_merge_branch(self):
        self.setupStep(
            Gitea(repourl='git@gitea.example.com:base/awesome_project.git',
                           mode='full', method='clean'))

        self.expectCommands(
            ExpectShell(workdir='wkdir',
                        command=['git', '--version'])
            + ExpectShell.log('stdio',
                              stdout='git version 1.7.5')
            + 0,
            Expect('stat', dict(file='wkdir/.buildbot-patched',
                                logEnviron=True))
            + 1,
            Expect('listdir', {'dir': 'wkdir', 'logEnviron': True,
                               'timeout': 1200})
            + Expect.update('files', ['.git'])
            + 0,
            ExpectShell(workdir='wkdir',
                        command=['git', 'clean', '-f', '-f', '-d'])
            + 0,
            # here we always ignore revision, and fetch the merge branch
            ExpectShell(workdir='wkdir',
                        command=['git', 'fetch', '-t',
                                 'git@gitea.example.com:base/awesome_project.git', 'HEAD'])
            + 0,
            ExpectShell(workdir='wkdir',
                        command=['git', 'reset', '--hard', 'FETCH_HEAD', '--'])
            + 0,
            ExpectShell(workdir='wkdir',
                        command=['git', 'config', 'remote.pr_source.url'])
            + 0,
            ExpectShell(workdir='wkdir',
                        command=['git', 'remote', 'add', 'pr_source', 'git@gitea.example.com:target/awesome_project.git'])
            + 0,
            ExpectShell(workdir='wkdir',
                        command=['git', 'fetch', 'pr_source'])
            + 0,
            ExpectShell(workdir='wkdir',
                        command=['git', 'merge', 'e4cd1224c622d46a8199c85c858485723115d2c8'])
            + 0,
            ExpectShell(workdir='wkdir',
                        command=['git', 'rev-parse', 'HEAD'])
            + ExpectShell.log('stdio',
                              stdout='e4cd1224c622d46a8199c85c858485723115d2c8')
            + 0,
        )
        self.expectOutcome(result=SUCCESS)
        self.expectProperty(
            'got_revision', 'e4cd1224c622d46a8199c85c858485723115d2c8', 'Gitea')
        return self.runStep()
