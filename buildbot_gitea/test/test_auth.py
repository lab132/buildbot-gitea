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

from buildbot_gitea.auth import GiteaAuth, GiteaAuthWithPermissions

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


class TestGiteaAuthWithPermissions(TestReactorMixin, www.WwwTestMixin, ConfigErrorsMixin,
                    unittest.TestCase):

    USER = {
        'avatar_url': 'http://pic',
        'email': 'bar@foo',
        'full_name': 'foo bar',
        'username': 'bar',
    }

    ORG1 = {
        "id": 1,
        "name": "Owners",
        "description": "",
        "organization": {
            "id": 1,
            "name": "org1",
            "full_name": "Organization 1",
            "email": "",
            "avatar_url": "https://gitea.com/avatars/sha1",
            "description": "",
            "website": "",
            "location": "",
            "visibility": "limited",
            "repo_admin_change_team_access": True,
            "username": "org1"
        },
        "includes_all_repositories": True,
        "permission": "owner",
        "units": [
            "repo.code",
            "repo.issues",
            "repo.ext_issues",
            "repo.pulls",
            "repo.releases",
            "repo.wiki",
            "repo.packages",
            "repo.ext_wiki",
            "repo.projects",
            "repo.actions"
        ],
        "units_map": {
            "repo.actions": "owner",
            "repo.code": "owner",
            "repo.ext_issues": "owner",
            "repo.ext_wiki": "owner",
            "repo.issues": "owner",
            "repo.packages": "owner",
            "repo.projects": "owner",
            "repo.pulls": "owner",
            "repo.releases": "owner",
            "repo.wiki": "owner"
        },
        "can_create_org_repo": True
    }
    ORG2 = {
        "id": 2,
        "name": "Users",
        "description": "Basic Users",
        "organization": {
            "id": 2,
            "name": "org2",
            "full_name": "Organization 2",
            "email": "",
            "avatar_url": "https://gitea.com/avatars/sha1",
            "description": "",
            "website": "https://confluence.dont-nod.com/display/DEV/",
            "location": "",
            "visibility": "limited",
            "repo_admin_change_team_access": False,
            "username": "org2"
        },
        "includes_all_repositories": False,
        "permission": "write",
        "units": [
            "repo.ext_issues",
            "repo.code",
            "repo.issues",
            "repo.pulls",
            "repo.releases",
            "repo.wiki",
            "repo.ext_wiki"
        ],
        "units_map": {
            "repo.code": "write",
            "repo.ext_issues": "read",
            "repo.ext_wiki": "read",
            "repo.issues": "write",
            "repo.pulls": "write",
            "repo.releases": "write",
            "repo.wiki": "write"
        },
        "can_create_org_repo": False
    }

    def setUp(self):
        self.setup_test_reactor()
        if requests is None:
            raise unittest.SkipTest("Need to install requests to test oauth2")

        self.patch(requests, 'request', mock.Mock(spec=requests.request))
        self.patch(requests, 'post', mock.Mock(spec=requests.post))
        self.patch(requests, 'get', mock.Mock(spec=requests.get))

        self.giteaAuth = GiteaAuthWithPermissions(
            'https://gitea.test',
            'client-id',
            'client-secret')
        self._master = master = self.make_master(
            url='h:/a/b/', auth=self.giteaAuth)
        self.giteaAuth.reconfigAuth(master, master.config)

        def mock_gitea_auth_get(session, path):
            return {
                "/api/v1/user": TestGiteaAuthWithPermissions.USER,
                "/api/v1/user/teams": [
                    TestGiteaAuthWithPermissions.ORG1,
                    TestGiteaAuthWithPermissions.ORG2,
                ],
            }.get(path)

        self.patch(self.giteaAuth, 'get', mock.Mock(
            spec=GiteaAuthWithPermissions.get,
            side_effect=mock_gitea_auth_get,
        ))

    @defer.inlineCallbacks
    def test_getGiteaUserOrgTeamPermissions(self):
        # won't be used
        fake_session = None
        res = yield self.giteaAuth.getUserInfoFromOAuthClient(fake_session)
        self.assertDictEqual(
            res,
            {
                'avatar_url': 'http://pic',
                'email': 'bar@foo',
                'full_name': 'foo bar',
                'username': 'bar',
                'organizations': {
                    'org1': {
                        'Owners': 'owner',
                    },
                    'org2': {
                        'Users': 'write',
                    },
                }
            },
        )
