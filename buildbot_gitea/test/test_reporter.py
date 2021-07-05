# Based on TestGitLabStatusPush from buildbot

from __future__ import absolute_import
from __future__ import print_function

from mock import Mock

from twisted.internet import defer
from twisted.trial import unittest

from buildbot import config
from buildbot.process.properties import Interpolate
from buildbot.process.results import FAILURE
from buildbot.process.results import SUCCESS
from buildbot_gitea.reporter import GiteaStatusPush
from buildbot.test.fake import fakemaster
from buildbot.test.fake import httpclientservice as fakehttpclientservice
from buildbot.test.util import logging
from buildbot.test.util.reporter import ReporterTestMixin
from buildbot.test.util.misc import TestReactorMixin



class TestGiteaStatusPush(
    unittest.TestCase,
    ReporterTestMixin,
    logging.LoggingMixin,
    TestReactorMixin):

    @defer.inlineCallbacks
    def setUp(self):
        self.setUpTestReactor()

        self.setup_reporter_test()

    # repository must be in the form http://gitea/<owner>/<project>
        self.reporter_test_repo = u'http://gitea/buildbot/buildbot'

        # ignore config error if txrequests is not installed
        self.patch(config, '_errors', Mock())
        self.master = fakemaster.make_master(testcase=self,
                                             wantData=True, wantDb=True, wantMq=True)

        yield self.master.startService()
        self._http = yield fakehttpclientservice.HTTPClientService.getService(
            self.master, self,
            "http://gitea", headers={'Authorization': 'token XXYYZZ'},
            debug=None, verify=None)
        self.sp = GiteaStatusPush("http://gitea/", Interpolate('XXYYZZ'))

        yield self.sp.setServiceParent(self.master)

    def tearDown(self):
        return self.master.stopService()

    def setupProps(self):
        self.reporter_test_props['owner'] = "buildbot"
        self.reporter_test_props['repository_name'] = "buildbot"

    @defer.inlineCallbacks
    def setupBuildResults(self, buildResults):
        self.insertTestData([buildResults], buildResults)
        build = yield self.master.data.get(("builds", 20))
        defer.returnValue(build)

    @defer.inlineCallbacks
    def test_basic(self):
        self.setupProps()
        build = yield self.setupBuildResults(SUCCESS)
        # we make sure proper calls to txrequests have been made
        self._http.expect(
            'post',
            '/api/v1/repos/buildbot/buildbot/statuses/d34db33fd43db33f',
            json={'state': 'pending',
                  'target_url': 'http://localhost:8080/#builders/79/builds/0',
                  'description': 'Build started.', 'context': 'buildbot/Builder0'})
        self._http.expect(
            'post',
            '/api/v1/repos/buildbot/buildbot/statuses/d34db33fd43db33f',
            json={'state': 'success',
                  'target_url': 'http://localhost:8080/#builders/79/builds/0',
                  'description': 'Build done.', 'context': 'buildbot/Builder0'})
        self._http.expect(
            'post',
            '/api/v1/repos/buildbot/buildbot/statuses/d34db33fd43db33f',
            json={'state': 'failure',
                  'target_url': 'http://localhost:8080/#builders/79/builds/0',
                  'description': 'Build done.', 'context': 'buildbot/Builder0'})

        build['complete'] = False
        self.sp._got_event(('builds', 20, 'new'), build)
        build['complete'] = True
        self.sp._got_event(('builds', 20, 'finished'), build)
        build['results'] = FAILURE
        self.sp._got_event(('builds', 20, 'finished'), build)

    @defer.inlineCallbacks
    def test_pullrequest(self):
        self.setupProps()
        self.reporter_test_props["pr_id"] = 42
        self.reporter_test_props["head_owner"] = 'foo'
        self.reporter_test_props["head_reponame"] = 'bar'
        self.reporter_test_props["head_sha"] = '52c7864e56d1425f4c0a76c1e692942047bdd849'
        build = yield self.setupBuildResults(SUCCESS)
        # we make sure proper calls to txrequests have been made
        self._http.expect(
            'post',
            '/api/v1/repos/foo/bar/statuses/52c7864e56d1425f4c0a76c1e692942047bdd849',
            json={'state': 'success',
                  'target_url': 'http://localhost:8080/#builders/79/builds/0',
                  'description': 'Build done.', 'context': 'buildbot/pull_request/Builder0'})

        build['complete'] = True
        self.sp._got_event(('builds', 20, 'finished'), build)
        
    @defer.inlineCallbacks
    def test_sshurl(self):
        self.setupProps()
        self.TEST_REPO = u'git@gitea:buildbot/buildbot.git'
        build = yield self.setupBuildResults(SUCCESS)
        # we make sure proper calls to txrequests have been made
        self._http.expect(
            'post',
            '/api/v1/repos/buildbot/buildbot/statuses/d34db33fd43db33f',
            json={'state': 'pending',
                  'target_url': 'http://localhost:8080/#builders/79/builds/0',
                  'description': 'Build started.', 'context': 'buildbot/Builder0'})
        build['complete'] = False
        self.sp._got_event(('builds', 20, 'new'), build)

    @defer.inlineCallbacks
    def test_sshurl_noprops(self):
        self.reporter_test_repo = u'git@gitea:buildbot/buildbot.git'
        build = yield self.setupBuildResults(SUCCESS)
        # we make sure proper calls to txrequests have been made
        self._http.expect(
            'post',
            '/api/v1/repos/buildbot/buildbot/statuses/d34db33fd43db33f',
            json={'state': 'pending',
                  'target_url': 'http://localhost:8080/#builders/79/builds/0',
                  'description': 'Build started.', 'context': 'buildbot/Builder0'})
        build['complete'] = False
        self.sp._got_event(('builds', 20, 'new'), build)

    @defer.inlineCallbacks
    def test_noowner(self):
        self.setUpLogging()
        self.setupProps()
        del self.reporter_test_props["owner"]
        self.TEST_REPO = u''
        build = yield self.setupBuildResults(SUCCESS)
        build['complete'] = False
        self.sp._got_event(('builds', 20, 'new'), build)
        # implicit check that no http request is done
        self.assertLogged("Could not send status, "
                    "build has no owner property for Gitea.")

    @defer.inlineCallbacks
    def test_noreponame(self):
        self.setUpLogging()
        self.setupProps()
        del self.reporter_test_props["repository_name"]
        self.TEST_REPO = u''
        build = yield self.setupBuildResults(SUCCESS)
        build['complete'] = False
        self.sp._got_event(('builds', 20, 'new'), build)
        # implicit check that no http request is done
        self.assertLogged("Could not send status, "
                    "build has no repository_name property for Gitea.")

    @defer.inlineCallbacks
    def test_senderror(self):
        self.setupProps()
        self.setUpLogging()
        build = yield self.insert_build_new()
        # we make sure proper calls to txrequests have been made
        self._http.expect(
            'post',
            '/api/v1/repos/buildbot/buildbot/statuses/d34db33fd43db33f',
            json={'state': 'pending',
                  'target_url': 'http://localhost:8080/#builders/79/builds/0',
                  'description': 'Build started.', 'context': 'buildbot/Builder0'},
            content_json={
                "message": "sha1 not found: d34db33fd43db33f",
                "url": "https://godoc.org/github.com/go-gitea/go-sdk/gitea"
            },
            code=500)
        build['complete'] = False
        self.sp._got_event(("builds", 20, "new"), build)
        self.assertLogged(
            "Could not send status \"pending\" for "
            "http://gitea/buildbot/buildbot at d34db33fd43db33f:"
            " 500 : sha1 not found: d34db33fd43db33f")

    @defer.inlineCallbacks
    def test_badchange(self):
        self.setupProps()
        self.setUpLogging()
        build = yield self.insert_build_new()
        # we make sure proper calls to txrequests have been made
        self._http.expect(
            'post',
            '/api/v1/repos/buildbot/buildbot/statuses/d34db33fd43db33f',
            json={
                'state': 'pending',
                'description': 'Build started.',
                'target_url': 'http://localhost:8080/#builders/79/builds/0',
                'context': 'buildbot/Builder0'
            },
            content_json={"message": "Not found"},
            code=404,
        )
        build['complete'] = False
        yield self.sp._got_event(("builds", 20, "new"), build)
        self.assertLogged("Could not send status \"pending\" for"
                          " http://gitea/buildbot/buildbot at d34db33fd43db33f")
        self.flushLoggedErrors(AssertionError)
