import json
import re
from buildbot.util import bytes2unicode
from buildbot.www.hooks.base import BaseHookHandler

from twisted.python import log

_HEADER_EVENT_TYPE = 'X-Gitea-Event'


class GiteaHandler(BaseHookHandler):

    def processPushEvent(self, payload, event_type, codebase):
        refname = payload["ref"]

        changes = []

        # We only care about regular heads or tags
        match = re.match(r"^refs/(heads|tags)/(.+)$", refname)
        if not match:
            log.msg("Ignoring refname `%s': Not a branch" % refname)
            return changes

        branch = match.group(2)

        repository = payload["repository"]
        repo_url = repository["html_url"]
        project = repository["full_name"]

        for commit in payload["commits"]:
            timestamp = commit["timestamp"]
            change = {
                'author': '%s <%s>'.format((commit['author']['name'],
                                            commit['author']['email'])),
                'comments': commit['message'],
                'revision': commit['id'],
                'when_timestamp': timestamp,
                'branch': branch,
                'revlink': commit['url'],
                'repository': repo_url,
                'project': project,
                'category': event_type,
                'properties': {
                    'event': event_type,
                },
            }
            log.msg("Adding commit: {}".format(str(change)))
            if codebase is not None:
                change['codebase'] = codebase
            changes.append(change)
        return changes

    def getChanges(self, request):
        secret = None
        if self.options is dict:
            secret = self.options.get("secret")

        try:
            content = request.content.read()
            payload = json.loads(bytes2unicode(content))
            log.msg("Payload:")
            log.msg(payload)
        except Exception as e:
            raise ValueError("Error loading JSON: " + str(e))
        if secret is not None and secret != payload["secret"]:
            raise ValueError("Invalid secret")

        event_type = bytes2unicode(request.getHeader(_HEADER_EVENT_TYPE))
        log.msg("Received event_type: {}".format(event_type))

        codebases = request.args.get("codebase", [None])
        codebase = bytes2unicode(codebases[0])

        changes = self.processPushEvent(payload, event_type, codebase)

        return (changes, "git")


# Plugin name
gitea = GiteaHandler
