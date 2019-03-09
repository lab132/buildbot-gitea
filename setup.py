#!/usr/bin/env python

from distutils.core import setup

setup(name='buildbot-gitea',
      version='0.1.0',
      description='buildbot plugin for integration with Gitea.',
      author='Marvin Pohl',
      author_email='marvin@lab132.com',
      url='https://lab132.com',
      packages=['buildbot_gitea'],
      install_requires=[
          "buildbot>=2.0.0"
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
