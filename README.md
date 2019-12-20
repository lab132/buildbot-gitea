# Buildbot Gitea Plugin


[![PyPI version](https://badge.fury.io/py/buildbot-gitea.svg)](https://badge.fury.io/py/buildbot-gitea)
![GitHub](https://img.shields.io/github/license/lab132/buildbot-gitea)
[![Build Status](https://travis-ci.org/lab132/buildbot-gitea.svg?branch=master)](https://travis-ci.org/lab132/buildbot-gitea)

This plugin for buildbot adds integration support with gitea, featuring push hooks, commit status updates and a change source.

# Installation
```
pip install buildbot_gitea
```

This installs itself into the plugin discovery of buildbot, so no extra imports are required to get buildbot to find the plugin.

# Configuration

The following configuration shows how the different parts of the plugin can be set-up in the buildbot master.cfg:

```py

from buildbot.plugins import *

c = BuildbotMasterConfig = {}
c['www'] = {
    'change_hook_dialects': {
        'gitea': {
            'secret': '<SecretToEnterInGitea>',
            'onlyIncludePushCommit': True
        }
    },
}

c['services'] = [
    # Report status back to gitea, verbose flag enables verbose output in logging for debugging
    reporters.GiteaStatusPush(
        'https://example.com', "SECRET", verbose=True)
]

buildFactory = util.BuildFactory()

factory.addStep(steps.Gitea(
    repourl="ssh://git@example.com/example_user/example_project.git",
    mode='incremental',
    workdir="build",
    branch="master",
    codebase='example_codebase',
    progress=True,
    logEnviron=False,
))
```

The webhook currently supports pushes and pull requests by default, but you can
subclass `buildbot_gitea.webhook.GiteaHandler` to add supports for other events,
and then use your subclass by setting the `class` parameter:

```py
# myhook.py

from buildbot_gitea.webhook import GiteaHandler
class MyGiteaHook(GiteaHandler)
    def process_whatever(self, payload, event_type, codebase):
        # This should be a list of dicts
        changes = []

        return changes

# master.cfg

from myhook import MyGiteaHook

c['www'] = {
    'change_hook_dialects': {
        'gitea': {
            'class': MyGiteaHook,
            # ...
        }
    }
}
```

Note that the handlers need to be named according to the scheme:
`process_{event}` (e.g., `process_create`, etc).

# Parameters

## Change Hook

The change hook is set as part of the `www` section in the `change_hook_dialects` named `gitea`.

| Parameter | Description |
| --- | --- |
| `secret` | The secret, which needs to be set in gitea |
| `onlyIncludePushCommit` | A push may have more than one commit associated with it. If this is true, only the newest (latest) commit of all received will be added as a change to buildbot. If this is set to false, all commits will inside the push will be added. |
| `class` | Set this if you want to use your own handler class (see above for details) |

In gitea in your project or organization and add a new webhook of type gitea.
Set the parameters as follows:

| Parameter | Value |
| --- | --- |
| Target URL  | https://example.com/change_hook/gitea/ |
| HTTP Method  | `POST` |
| POST Content Type  | `application/json` |
| Secret  | The `secret` from above |

## Change Source

The change source is part build step to clone a gitea repository. It includes features to build a pull request, if the pull request can be merged without conflicts. This needs to be used in conjunction with a gitea `change_hook` and have it send pull request updates in order to be able  to handle pull requests.

The parameters for this are identical to the default [`git`](http://docs.buildbot.net/latest/manual/configuration/buildsteps.html#git) step from buildbot. It just uses information provided by the gitea `change_hook` to be able to handle pull requests.

## Reporter

The reporter sets the commit status of a commit inside of gitea, so in gitea a small icon will be displayed next to the commit message, indicating the build status.

The `GiteaStatusPush` is added to the `services` section of the global master config.

The parameters are as follows:

| Parameter | Value |
| --- | --- |
| URL | The URL to the gitea instance. |
| `token` | Generate an access token in the profile you want the buildbot to impersonate. Make sure the account in gitea has access to the repositories. |
| `startDescription` | `Renderable` A short description when buildbot starts building on a change. Defaults to `Build started.` |
| `endDescription` | `Renderable` A short description when buildbot stops building on a change. Defaults to `Build done.` |
| `context` | `Renderable` The context is an identifier for this status, allowing to identify from which builder this came, defaults to `Interpolate('buildbot/%(prop:buildername)s')` |
| `context_pr` | `Renderable` The context message to use, when building on a pull request, allowing to identify from which builder this came, defaults to `Interpolate('buildbot/pull_request/%(prop:buildername)s')` |
| `warningAsSuccess` | Treat warnings as build as success to set in the build status of gitea. If false, warnings will be displayed as warnings. |
| `verbose` | Perform verbose output |

## Authentication

Gitea supports OAuth2 authentication so it is possible to have buildbot communicate to Gitea to authenticate the user.

`./master.cfg`

```py
from buildbot.plugins import util
c['www']['auth'] = util.GiteaAuth(
    endpoint="https://your-gitea-host",
    client_id='oauth2-client-id',
    client_secret='oauth2-client-secret')
```

| Parameter | Value |
| --- | --- |
| `endpoint` | The URL to your Gitea app. Something like `https://gitea.example.com/` |
| `client_id` | The OAuth2 Client ID `GUID`, can be a `Secret`. |
| `client_secret` | The OAuth2 Client Secret provided, when creating the OAuth application in gitea. Can be a `Secret`. |

Resources:

+ [Gitea OAuth2 Provider documentation](https://docs.gitea.io/en-us/oauth2-provider/)
+ [Buildbot OAuth2 documentation](https://docs.buildbot.net/current/developer/cls-auth.html?highlight=oauth2#buildbot.www.oauth2.OAuth2Auth)