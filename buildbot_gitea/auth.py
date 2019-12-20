from buildbot.www.oauth2 import OAuth2Auth
from urllib.parse import urljoin


class GiteaAuth(OAuth2Auth):
    name = 'Gitea'
    faIcon = 'mug-tea'

    AUTH_URL = 'login/oauth/authorize'
    TOKEN_URL = 'login/oauth/access_token'

    def __init__(self, endpoint, client_id, client_secret):
        super(GiteaAuth, self).__init__(client_id, client_secret)
        self.resourceEndpoint = endpoint
        self.authUri = urljoin(endpoint, self.AUTH_URL)
        self.tokenUri = urljoin(endpoint, self.TOKEN_URL)

    def getUserInfoFromOAuthClient(self, c):
        return self.get(c, '/api/v1/user')
