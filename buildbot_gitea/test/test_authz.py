from twisted.trial import unittest
from buildbot_gitea.authz import RolesFromGitea


class TestGiteaAuthz_RolesFromGitea(unittest.TestCase):

    def test_RolesFromGitea_NoMatch(self):
        user_detail = {}

        role_provider = RolesFromGitea(
            roles=["test"],
            orgs=["org1"],
        )
        res = role_provider.getRolesFromUser(user_detail)
        self.assertNot(res)

        role_provider = RolesFromGitea(
            roles=["test"],
            teams=["team1"],
        )
        res = role_provider.getRolesFromUser(user_detail)
        self.assertNot(res)

        role_provider = RolesFromGitea(
            roles=["test"],
            permissions=["owner"],
        )
        res = role_provider.getRolesFromUser(user_detail)
        self.assertNot(res)

    def test_RolesFromGitea_Match(self):
        user_detail = {
            'organizations': {
                'org1': {
                    'Owners': 'owner',
                },
                'org2': {
                    'Users': 'write',
                },
            }
        }

        role_provider = RolesFromGitea(
            roles=["test"],
            orgs=["org1"],
        )
        res = role_provider.getRolesFromUser(user_detail)
        self.assertEqual(res, ["test"])

        role_provider = RolesFromGitea(
            roles=["test"],
            teams=["Owners"],
        )
        res = role_provider.getRolesFromUser(user_detail)
        self.assertEqual(res, ["test"])

        role_provider = RolesFromGitea(
            roles=["test"],
            permissions=["owner"],
        )
        res = role_provider.getRolesFromUser(user_detail)
        self.assertEqual(res, ["test"])

        role_provider = RolesFromGitea(
            roles=["test"],
            orgs=["org1"],
            teams=["Owners"],
            permissions=["owner"],
        )
        res = role_provider.getRolesFromUser(user_detail)
        self.assertEqual(res, ["test"])
