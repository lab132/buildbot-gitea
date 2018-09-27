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


class TestGiteaStatusPush(
    unittest.TestCase,
    ReporterTestMixin,
    logging.LoggingMixin):
    # repository must be in the form http://gitea/<owner>/<project>
    TEST_REPO = u'http://gitea/buildbot/buildbot'

    @defer.inlineCallbacks
    def setUp(self):
        # ignore config error if txrequests is not installed
        self.patch(config, '_errors', Mock())
        self.master = fakemaster.make_master(testcase=self,
                                             wantData=True, wantDb=True, wantMq=True)

        yield self.master.startService()
        self._http = yield fakehttpclientservice.HTTPClientService.getFakeService(
            self.master, self,
            "http://gitea", headers={'AuthorizationHeaderToken': 'token XXYYZZ'},
            debug=None, verify=None)
        self.sp = sp = GiteaStatusPush("http://gitea/", Interpolate('XXYYZZ'))
        sp.sessionFactory = Mock(return_value=Mock())

        yield sp.setServiceParent(self.master)

    def tearDown(self):
        return self.master.stopService()

    def setupProps(self):
        self.TEST_PROPS['owner'] = "buildbot"
        self.TEST_PROPS['repository_name'] = "buildbot"

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
                  'description': 'Build started.', 'name': 'buildbot/Builder0'})
        self._http.expect(
            'post',
            '/api/v1/repos/buildbot/buildbot/statuses/d34db33fd43db33f',
            json={'state': 'success',
                  'target_url': 'http://localhost:8080/#builders/79/builds/0',
                  'description': 'Build done.', 'name': 'buildbot/Builder0'})
        self._http.expect(
            'post',
            '/api/v1/repos/buildbot/buildbot/statuses/d34db33fd43db33f',
            json={'state': 'failure',
                  'target_url': 'http://localhost:8080/#builders/79/builds/0',
                  'description': 'Build done.', 'name': 'buildbot/Builder0'})

        build['complete'] = False
        self.sp.buildStarted(("build", 20, "started"), build)
        build['complete'] = True
        self.sp.buildFinished(("build", 20, "finished"), build)
        build['results'] = FAILURE
        self.sp.buildFinished(("build", 20, "finished"), build)

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
                  'description': 'Build started.', 'name': 'buildbot/Builder0'})
        build['complete'] = False
        self.sp.buildStarted(("build", 20, "started"), build)

    @defer.inlineCallbacks
    def test_sshurl_noprops(self):
        self.TEST_REPO = u'git@gitea:buildbot/buildbot.git'
        build = yield self.setupBuildResults(SUCCESS)
        # we make sure proper calls to txrequests have been made
        self._http.expect(
            'post',
            '/api/v1/repos/buildbot/buildbot/statuses/d34db33fd43db33f',
            json={'state': 'pending',
                  'target_url': 'http://localhost:8080/#builders/79/builds/0',
                  'description': 'Build started.', 'name': 'buildbot/Builder0'})
        build['complete'] = False
        self.sp.buildStarted(("build", 20, "started"), build)

    @defer.inlineCallbacks
    def test_noowner(self):
        self.setUpLogging()
        self.setupProps()
        del self.TEST_PROPS["owner"]
        self.TEST_REPO = u''
        build = yield self.setupBuildResults(SUCCESS)
        build['complete'] = False
        self.sp.buildStarted(("build", 20, "started"), build)
        # implicit check that no http request is done
        self.assertLogged("Could not send status, "
                    "build has no owner property for Gitea.")

    @defer.inlineCallbacks
    def test_noreponame(self):
        self.setUpLogging()
        self.setupProps()
        del self.TEST_PROPS["repository_name"]
        self.TEST_REPO = u''
        build = yield self.setupBuildResults(SUCCESS)
        build['complete'] = False
        self.sp.buildStarted(("build", 20, "started"), build)
        # implicit check that no http request is done
        self.assertLogged("Could not send status, "
                    "build has no repository_name property for Gitea.")

    @defer.inlineCallbacks
    def test_senderror(self):
        self.setupProps()
        self.setUpLogging()
        build = yield self.setupBuildResults(SUCCESS)
        # we make sure proper calls to txrequests have been made
        self._http.expect(
            'post',
            '/api/v1/repos/buildbot/buildbot/statuses/d34db33fd43db33f',
            json={'state': 'pending',
                  'target_url': 'http://localhost:8080/#builders/79/builds/0',
                  'description': 'Build started.', 'name': 'buildbot/Builder0'},
            content_json={'message': 'sha1 not found for branch master'},
            code=404)
        build['complete'] = False
        self.sp.buildStarted(("build", 20, "started"), build)
        self.assertLogged(
            "Could not send status \"pending\" for "
            "http://gitea/buildbot/buildbot at d34db33fd43db33f:"
            " sha1 not found for branch master")

    @defer.inlineCallbacks
    def test_badchange(self):
        self.setupProps()
        self.setUpLogging()
        build = yield self.setupBuildResults(SUCCESS)
        # we make sure proper calls to txrequests have been made
        build['complete'] = False
        self.sp.buildStarted(("build", 20, "started"), build)
        self.assertLogged("Failed to send status \"pending\" for"
                          " http://gitea/buildbot/buildbot at d34db33fd43db33f")
        self.flushLoggedErrors(AssertionError)
