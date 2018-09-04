#!/usr/bin/env python

from distutils.core import setup

setup(name='buildbot-gitea',
      version='0.0.1',
      description='buildbot plugin for integration with Gitea.',
      author='Marvin Pohl',
      author_email='marvin@lab132.com',
      url='https://lab132.com',
      packages=['gitea'],
      entry_points={
        "buildbot.webhooks": [
            "gitea = gitea.webhook:gitea"
        ]
      },
      )
