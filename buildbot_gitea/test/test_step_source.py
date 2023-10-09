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
from buildbot.test.steps import Expect
from buildbot.test.steps import ExpectShell
from buildbot.test.steps import ExpectListdir
from buildbot.test.util import config
from buildbot.test.util import sourcesteps
from buildbot.test.reactor import TestReactorMixin



class TestGitea(sourcesteps.SourceStepMixin, config.ConfigErrorsMixin, unittest.TestCase, TestReactorMixin):
    stepClass = Gitea

    def setUp(self):
        self.setup_test_reactor()
        self.sourceName = self.stepClass.__name__
        return self.setUpSourceStep()

    def setupStep(self, step, **kwargs):
        step = sourcesteps.SourceStepMixin.setup_step(self, step, **kwargs)
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

        self.expect_commands(
            ExpectShell(workdir='wkdir',
                        command=['git', '--version'])
            .stdout('git version 1.7.5').exit(0),
            Expect('stat', dict(file='wkdir/.buildbot-patched',
                                logEnviron=True)).exit(1),
            #+ Expect.update('files', ['.git'])
            ExpectListdir('wkdir').exit(0),
            ExpectShell(workdir='wkdir',
                        command=['git', 'clean', '-f', '-f', '-d']).exit(0),
            # here we always ignore revision, and fetch the merge branch
            ExpectShell(workdir='wkdir',
                        command=['git', 'fetch', '-f', '-t',
                                 'git@gitea.example.com:base/awesome_project.git', 'HEAD', '--progress'])
            .exit(0),
            ExpectShell(workdir='wkdir',
                        command=['git', 'reset', '--hard', 'FETCH_HEAD', '--'])
            .exit(0),
            ExpectShell(workdir='wkdir',
                        command=['git', 'config', 'remote.pr_source.url'])
            .exit(0),
            ExpectShell(workdir='wkdir',
                        command=['git', 'remote', 'add', 'pr_source', 'git@gitea.example.com:target/awesome_project.git'])
            .exit(0),
            ExpectShell(workdir='wkdir',
                        command=['git', 'fetch', 'pr_source'])
            .exit(0),
            ExpectShell(workdir='wkdir',
                        command=['git', 'merge', 'e4cd1224c622d46a8199c85c858485723115d2c8'])
            .exit(0),
            ExpectShell(workdir='wkdir',
                        command=['git', 'rev-parse', 'HEAD'])
            .stdout('e4cd1224c622d46a8199c85c858485723115d2c8').exit(0)
        )
        self.expect_outcome(result=SUCCESS)
        self.expect_property(
            'got_revision', 'e4cd1224c622d46a8199c85c858485723115d2c8', 'Gitea')
        return self.run_step()
