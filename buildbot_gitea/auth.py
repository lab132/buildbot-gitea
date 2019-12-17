from buildbot.www.oauth2 import OAuth2Auth
import urllib.parse

class GiteaAuth(OAuth2Auth):
    name = 'Gitea'
    faIcon = 'mug-tea'

    def __init__(self, endpoint, client_id, client_secret):
        super(__class__, self).__init__(client_id, client_secret)
        self.resourceEndpoint = endpoint
        self.authUri = urllib.parse.urljoin(endpoint, 'login/oauth/authorize')
        self.tokenUri = urllib.parse.urljoin(endpoint, 'login/oauth/access_token')

    def getUserInfoFromOAuthClient(self, c):
        return self.get(c, '/api/v1/user')