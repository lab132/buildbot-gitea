# Based on the gitlab reporter from buildbot

from __future__ import absolute_import
from __future__ import print_function

from twisted.internet import defer
from twisted.python import log

from buildbot.process.properties import Interpolate
from buildbot.process.properties import Properties
from buildbot.process.results import CANCELLED
from buildbot.process.results import EXCEPTION
from buildbot.process.results import FAILURE
from buildbot.process.results import RETRY
from buildbot.process.results import SKIPPED
from buildbot.process.results import SUCCESS
from buildbot.process.results import WARNINGS
from buildbot.reporters import http
from buildbot.util import httpclientservice
from buildbot.warnings import warn_deprecated
from buildbot.reporters.generators.build import BuildStartEndStatusGenerator
from buildbot.reporters.message import MessageFormatterRenderable

import re


class GiteaStatusPush(http.ReporterBase):
    name = "GiteaStatusPush"
    ssh_url_match = re.compile(r"(ssh://)?[\w+\-\_]+@[\w\.\-\_]+:?(\d*/)?(?P<owner>[\w_\-\.]+)/(?P<repo_name>[\w_\-\.]+?)(\.git)?$")

    def checkConfig(self, baseURL, token,
                    context=None, context_pr=None, verbose=False,
                    debug=None, verify=None,
                    generators=None,
                    warningAsSuccess=False, **kwargs):

        if generators is None:
            generators = self._create_default_generators()

        super().checkConfig(generators=generators, **kwargs)
        httpclientservice.HTTPClientService.checkAvailable(
            self.__class__.__name__)

    @defer.inlineCallbacks
    def reconfigService(self, baseURL, token,
                        context=None, context_pr=None, verbose=False,
                        debug=None, verify=None,
                        generators=None,
                        warningAsSuccess=False, **kwargs):

        token = yield self.renderSecrets(token)
        self.debug = debug
        self.verify = verify
        self.verbose = verbose
        if generators is None:
            generators = self._create_default_generators()

        yield super().reconfigService(generators=generators, **kwargs)

        self.context = context or Interpolate('buildbot/%(prop:buildername)s')
        self.context_pr = context_pr or \
            Interpolate('buildbot/pull_request/%(prop:buildername)s')
        if baseURL.endswith('/'):
            baseURL = baseURL[:-1]
        self.baseURL = baseURL
        self._http = yield httpclientservice.HTTPClientService.getService(
            self.master, baseURL,
            headers={'Authorization': 'token {}'.format(token)},
            debug=self.debug, verify=self.verify)
        self.verbose = verbose
        self.project_ids = {}
        self.warningAsSuccess = warningAsSuccess

    def _create_default_generators(self):
        start_formatter = MessageFormatterRenderable('Build started.')
        end_formatter = MessageFormatterRenderable('Build done.')

        return [
            BuildStartEndStatusGenerator(start_formatter=start_formatter,
                                         end_formatter=end_formatter)
        ]

    def createStatus(self,
                     project_owner, repo_name, sha, state, target_url=None,
                     description=None, context=None):
        """
        :param project_owner: username of the owning user or organization
        :param repo_name: name of the repository
        :param sha: Full sha to create the status for.
        :param state: one of the following 'pending', 'success', 'failed'
                      or 'cancelled'.
        :param target_url: Target url to associate with this status.
        :param description: Short description of the status.
        :param context: Context of the result
        :return: A deferred with the result from GitLab.

        """
        payload = {'state': state}

        if description is not None:
            payload['description'] = description

        if target_url is not None:
            payload['target_url'] = target_url

        if context is not None:
            payload['context'] = context

        return self._http.post(
            '/api/v1/repos/{owner}/{repository}/statuses/{sha}'.format(
                owner=project_owner,
                repository=repo_name,
                sha=sha
            ),
            json=payload)

    @defer.inlineCallbacks
    def send(self, build):
        # the only case when this function is called is when the user derives this class, overrides
        # send() and calls super().send(build) from there.
        yield self._send_impl(build)

    @defer.inlineCallbacks
    def sendMessage(self, reports):
        build = reports[0]['builds'][0]
        if self.send.__func__ is not GiteaStatusPush.send:
            warn_deprecated('2.9.0', 'send() in reporters has been deprecated. Use sendMessage()')
            yield self.send(build)
        else:
            yield self._send_impl(reports)

    @defer.inlineCallbacks
    def _send_impl(self, reports):
        report = reports[0]
        build = report['builds'][0]
        props = Properties.fromDict(build['properties'])
        props.master = self.master

        description = report.get('body', None)

        if build['complete']:
            state = {
                SUCCESS: 'success',
                WARNINGS: 'success' if self.warningAsSuccess else 'warning',
                FAILURE: 'failure',
                SKIPPED: 'success',
                EXCEPTION: 'error',
                RETRY: 'pending',
                CANCELLED: 'error'
            }.get(build['results'], 'failure')
        else:
            state = 'pending'

        if 'pr_id' in props:
            context = yield props.render(self.context_pr)
        else:
            context = yield props.render(self.context)

        sourcestamps = build['buildset']['sourcestamps']

        for sourcestamp in sourcestamps:
            sha = sourcestamp['revision']
            repository_owner = None
            if sha is None:
                # No special revision for this, so ignore it
                continue
            # If this is a pull request, send the status to the head repository
            if 'pr_id' in props:
                repository_name = props['head_reponame']
                repository_owner = props['head_owner']
                sha = props['head_sha']
            elif 'repository_name' in props:
                repository_name = props['repository_name']
            else:
                match = re.match(self.ssh_url_match, sourcestamp['repository'])
                if match is not None:
                    repository_name = match.group("repo_name")
                else:
                    log.msg(
                        "Could not send status, "
                        "build has no repository_name property for Gitea.")
                    continue
            if repository_owner is None:
                if 'owner' in props:
                    repository_owner = props['owner']
                else:
                    match = re.match(self.ssh_url_match, sourcestamp['repository'])
                    if match is not None:
                        repository_owner = match.group("owner")
                    else:
                        log.msg(
                            "Could not send status, "
                            "build has no owner property for Gitea.")
                        continue
            try:
                target_url = build['url']
                res = yield self.createStatus(
                    project_owner=repository_owner,
                    repo_name=repository_name,
                    sha=sha,
                    state=state,
                    target_url=target_url,
                    context=context,
                    description=description
                )
                if res.code not in (200, 201, 204):
                    message = yield res.json()
                    message = message.get('message', 'unspecified error')
                    log.msg(
                        'Could not send status "{state}" for '
                        '{repo} at {sha}: {code} : {message}'.format(
                            state=state,
                            repo=sourcestamp['repository'], sha=sha,
                            code=res.code,
                            message=message))
                elif self.verbose:
                    log.msg(
                        'Status "{state}" sent for '
                        '{repo} at {sha}.'.format(
                            state=state,
                            repo=sourcestamp['repository'], sha=sha))
            except Exception as e:
                log.err(
                    e,
                    'Failed to send status "{state}" for '
                    '{repo} at {sha}'.format(
                        state=state,
                        repo=sourcestamp['repository'], sha=sha
                    ))
