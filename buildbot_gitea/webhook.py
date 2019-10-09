import json
import re
from buildbot.util import bytes2unicode
from buildbot.www.hooks.base import BaseHookHandler

from twisted.python import log
from dateutil.parser import parse as dateparse

_HEADER_EVENT_TYPE = 'X-Gitea-Event'


class GiteaHandler(BaseHookHandler):

    def process_push(self, payload, event_type, codebase):
        refname = payload["ref"]

        changes = []

        # We only care about regular heads or tags
        match = re.match(r"^refs/(heads|tags)/(.+)$", refname)
        if not match:
            log.msg("Ignoring refname '{}': Not a branch or tag".format(refname))
            return changes

        branch = match.group(2)

        repository = payload['repository']
        repo_url = repository['ssh_url']
        project = repository['full_name']

        commits = payload['commits']
        if isinstance(self.options, dict) and self.options.get('onlyIncludePushCommit', False):
            commits = commits[:1]

        for commit in commits:
            timestamp = dateparse(commit['timestamp'])
            change = {
                'author': '{} <{}>'.format(commit['author']['name'],
                                           commit['author']['email']),
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
                    'repository_name': repository['name'],
                    'owner': repository["owner"]["username"]
                },
            }
            if codebase is not None:
                change['codebase'] = codebase
            changes.append(change)
        return changes

    def process_pull_request(self, payload, event_type, codebase):
        action = payload['action']

        # Only handle potential new stuff, ignore close/.
        # Merge itself is handled by the regular branch push message
        if action not in ['opened', 'synchronized', 'edited', 'reopened']:
            log.msg("Gitea Pull Request event '{}' ignored".format(action))
            return []
        pull_request = payload['pull_request']
        if not pull_request['mergeable']:
            log.msg("Gitea Pull Request ignored because it is not mergeable.")
            return []
        if pull_request['merged']:
            log.msg("Gitea Pull Request ignored because it is already merged.")
            return []
        timestamp = dateparse(pull_request['updated_at'])
        base = pull_request['base']
        head = pull_request['head']
        repository = payload['repository']
        change = {
            'author': '{} <{}>'.format(pull_request['user']['full_name'],
                                       pull_request['user']['email']),
            'comments': 'PR#{}: {}\n\n{}'.format(
                pull_request['number'],
                pull_request['title'],
                pull_request['body']),
            'revision': head['sha'],
            'when_timestamp': timestamp,
            'branch': head['ref'],
            'revlink': pull_request['html_url'],
            'repository': repository['ssh_url'],
            'project': repository['full_name'],
            'category': event_type,
            'properties': {
                'event': event_type,
                'base_branch': base['ref'],
                'base_sha': base['sha'],
                'base_repo_id': base['repo_id'],
                'base_repository': base['repo']['clone_url'],
                'base_git_ssh_url': base['repo']['ssh_url'],
                'head_branch': head['ref'],
                'head_sha': head['sha'],
                'head_repo_id': head['repo_id'],
                'head_repository': head['repo']['clone_url'],
                'head_git_ssh_url': head['repo']['ssh_url'],
                'pr_id': pull_request['id'],
                'pr_number': pull_request['number'],
                'repository_name': repository['name'],
                'owner': repository["owner"]["username"],
            },
        }
        if codebase is not None:
            change['codebase'] = codebase
        return [change]

    def getChanges(self, request):
        secret = None
        if isinstance(self.options, dict):
            secret = self.options.get('secret')
        try:
            content = request.content.read()
            payload = json.loads(bytes2unicode(content))
        except Exception as exception:
            raise ValueError('Error loading JSON: ' + str(exception))
        if secret is not None and secret != payload['secret']:
            raise ValueError('Invalid secret')
        event_type = bytes2unicode(request.getHeader(_HEADER_EVENT_TYPE))
        log.msg("Received event '{}' from gitea".format(event_type))

        codebases = request.args.get('codebase', [None])
        codebase = bytes2unicode(codebases[0])
        changes = []

        handler_function = getattr(self, 'process_{}'.format(event_type), None)
        if not handler_function:
            log.msg("Ignoring gitea event '{}'".format(event_type))
        else:
            changes = handler_function(payload, event_type, codebase)

        return (changes, 'git')


class GiteaHandlerPlugin(BaseHookHandler):
    def __init__(self, master, options):
        if not options:
            options = {}
        super().__init__(master, options)

        handler_class = options.get('class', GiteaHandler)
        if 'class' in options:
            del options['class']

        self.handler = handler_class(master, options)

    def getChanges(self, request):
        return self.handler.getChanges(request)

# Plugin name
gitea = GiteaHandlerPlugin
