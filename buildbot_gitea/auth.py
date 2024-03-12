from buildbot.www.oauth2 import OAuth2Auth
from urllib.parse import urljoin


class GiteaAuth(OAuth2Auth):
    name = 'Gitea'
    faIcon = 'fa-coffee'

    AUTH_URL = 'login/oauth/authorize'
    TOKEN_URL = 'login/oauth/access_token'

    def __init__(self, endpoint, client_id, client_secret, **kwargs):
        super(GiteaAuth, self).__init__(client_id, client_secret, **kwargs)
        self.resourceEndpoint = endpoint
        self.authUri = urljoin(endpoint, self.AUTH_URL)
        self.tokenUri = urljoin(endpoint, self.TOKEN_URL)

    def getUserInfoFromOAuthClient(self, c):
        return self.get(c, '/api/v1/user')


class GiteaAuthWithPermissions(GiteaAuth):
    def getUserInfoFromOAuthClient(self, c):
        user_info = super(GiteaAuthWithPermissions, self).getUserInfoFromOAuthClient(c)

        teams_info = self.get(c, '/api/v1/user/teams')

        user_organizations = user_info.setdefault("organizations", {})
        for team in teams_info:
            org = team.get("organization")
            if org is None:
                continue
            user_organizations.setdefault(
                org["name"], {}
            )[team["name"]] = team["permission"]

        return user_info
