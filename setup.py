#!/usr/bin/env python

from distutils.core import setup

VERSION = "0.1.0"

setup(name='buildbot-gitea',
      version=VERSION,
      description='buildbot plugin for integration with Gitea.',
      author='Marvin Pohl',
      author_email='hello@lab132.com',
      url='https://github.com/lab132/buildbot-gitea',
      packages=['buildbot_gitea'],
      requires=[
          "buildbot (>=2.0.0)"
      ],
      entry_points={
          "buildbot.webhooks": [
              "gitea = buildbot_gitea.webhook:gitea"
          ],
          "buildbot.steps": [
              "Gitea = buildbot_gitea.step_source:Gitea"
          ],
          "buildbot.reporters": [
              "GiteaStatusPush = buildbot_gitea.reporter:GiteaStatusPush"
          ]
      },
      )
