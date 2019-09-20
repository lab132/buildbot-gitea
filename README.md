# Buildbot Gitea Plugin

[![PyPI version](https://badge.fury.io/py/buildbot-gitea.svg)](https://badge.fury.io/py/buildbot-gitea)
![GitHub](https://img.shields.io/github/license/lab132/buildbot-gitea)

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

# Parameters

## Change Hook

The change hook is set as part of the `www` section in the `change_hook_dialects` named `gitea`.

| Parameter | Description |
| --- | --- |
| `secret` | The secret, which needs to be set in gitea |
| `onlyIncludePushCommit` | A push may have more than one commit associated with it. If this is true, only the newest (latest) commit of all received will be added as a change to buildbot. If this is set to false, all commits will inside the push will be added. |

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