#!/usr/bin/env python

from setuptools import setup


with open("README.md", "r") as fh:
    long_description = fh.read()

VERSION = "1.8.0"

setup(name='buildbot-gitea',
      version=VERSION,
      description='buildbot plugin for integration with Gitea.',
      author='Marvin Pohl',
      author_email='hello@lab132.com',
      url='https://github.com/lab132/buildbot-gitea',
      long_description=long_description,
      long_description_content_type="text/markdown",
      packages=['buildbot_gitea'],
      install_requires=[
          "buildbot>=3.9.2"
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
          ],
          "buildbot.util": [
              "GiteaAuth = buildbot_gitea.auth:GiteaAuth",
              "GiteaAuthWithPermissions = buildbot_gitea.auth:GiteaAuthWithPermissions",
              "RolesFromGitea = buildbot_gitea.authz:RolesFromGitea"
          ]
      },
      classifiers=[
          "Development Status :: 5 - Production/Stable",
          "Environment :: Plugins",
          "Intended Audience :: Developers",
          "License :: OSI Approved :: MIT License",
          "Operating System :: Microsoft :: Windows",
          "Operating System :: MacOS",
          "Operating System :: POSIX :: Linux",
          "Topic :: Software Development :: Build Tools",
      ]
      )
