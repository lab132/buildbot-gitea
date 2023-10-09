import json
import mock
from buildbot.process.properties import Secret
from buildbot.test.util.config import ConfigErrorsMixin
from buildbot.test.reactor import TestReactorMixin
from buildbot.test.util import www
from twisted.internet import defer
from twisted.trial import unittest
from buildbot.secrets.manager import SecretManager
from buildbot.test.fake.secrets import FakeSecretStorage

from buildbot_gitea.auth import GiteaAuth

try:
    import requests
except ImportError:
    requests = None


class FakeResponse:

    def __init__(self, _json):
        self.json = lambda: _json
        self.content = json.dumps(_json)

    def raise_for_status(self):
        pass


class TestGiteaAuth(TestReactorMixin, www.WwwTestMixin, ConfigErrorsMixin,
                    unittest.TestCase):
    def setUp(self):
        self.setup_test_reactor()
        if requests is None:
            raise unittest.SkipTest("Need to install requests to test oauth2")

        self.patch(requests, 'request', mock.Mock(spec=requests.request))
        self.patch(requests, 'post', mock.Mock(spec=requests.post))
        self.patch(requests, 'get', mock.Mock(spec=requests.get))

        self.giteaAuth = GiteaAuth(
            'https://gitea.test',
            'client-id',
            'client-secret')
        self._master = master = self.make_master(
            url='h:/a/b/', auth=self.giteaAuth)
        self.giteaAuth.reconfigAuth(master, master.config)

        self.giteaAuth_secret = GiteaAuth(
            'https://gitea.test',
            Secret("client-id"),
            Secret("client-secret"))
        self._master = master = self.make_master(
            url='h:/a/b/', auth=self.giteaAuth_secret)
        fake_storage_service = FakeSecretStorage()
        fake_storage_service.reconfigService(
            secretdict={
                "client-id": "secretClientId",
                "client-secret": "secretClientSecret"
            })
        secret_service = SecretManager()
        secret_service.services = [fake_storage_service]
        secret_service.setServiceParent(self._master)
        self.giteaAuth_secret.reconfigAuth(master, master.config)

    @defer.inlineCallbacks
    def test_getGiteaLoginURL(self):
        res = yield self.giteaAuth.getLoginURL('http://redir')
        exp = ("https://gitea.test/login/oauth/authorize?client_id=client-id&"
               "redirect_uri=h%3A%2Fa%2Fb%2Fauth%2Flogin&response_type=code&"
               "state=redirect%3Dhttp%253A%252F%252Fredir")
        self.assertEqual(res, exp)
        res = yield self.giteaAuth.getLoginURL(None)
        exp = ("https://gitea.test/login/oauth/authorize?client_id=client-id&"
               "redirect_uri=h%3A%2Fa%2Fb%2Fauth%2Flogin&response_type=code")
        self.assertEqual(res, exp)

    @defer.inlineCallbacks
    def test_getGiteaLoginURL_with_secret(self):
        res = yield self.giteaAuth_secret.getLoginURL('http://redir')
        exp = ("https://gitea.test/login/oauth/authorize?client_id=secretClientId&"
               "redirect_uri=h%3A%2Fa%2Fb%2Fauth%2Flogin&response_type=code&"
               "state=redirect%3Dhttp%253A%252F%252Fredir")
        self.assertEqual(res, exp)
        res = yield self.giteaAuth_secret.getLoginURL(None)
        exp = ("https://gitea.test/login/oauth/authorize?client_id=secretClientId&"
               "redirect_uri=h%3A%2Fa%2Fb%2Fauth%2Flogin&response_type=code")
        self.assertEqual(res, exp)
