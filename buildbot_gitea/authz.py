from buildbot.www.authz.roles import RolesFromBase

class RolesFromGitea(RolesFromBase):
    def __init__(self, roles, orgs=None, teams=None, permissions=None):
        self.roles = roles
        self.orgs = orgs
        self.teams = teams
        self.permissions = permissions

        if not any(e is not None and len(e) > 0 for e in [
            self.orgs,
            self.teams,
            self.permissions,
        ]):
            from buildbot import config
            config.error('RolesFromGitea require one valid of orgs, teams or permissions')


    def getRolesFromUserPermissions(self, user_permissions):
        if self.permissions is None or user_permissions in self.permissions:
            return self.roles

        return None

    def getRolesFromUserTeam(self, user_teams):
        check_teams = self.teams if self.teams is not None else user_teams.keys()
        for team in check_teams:
            user_permissions = user_teams.get(team)
            if user_permissions is None:
                continue

            roles = self.getRolesFromUserPermissions(user_permissions)
            if roles is not None:
                return roles

        return None

    def getRolesFromUserOrg(self, user_orgs):
        check_orgs = self.orgs if self.orgs is not None else user_orgs.keys()
        for org in check_orgs:
            user_teams = user_orgs.get(org)
            if user_teams is None:
                continue

            roles = self.getRolesFromUserTeam(user_teams)
            if roles is not None:
                return roles

        return None

    def getRolesFromUser(self, userDetails):
        user_orgs = userDetails.get("organizations", {})
        roles = self.getRolesFromUserOrg(user_orgs)
        if roles is not None:
            return roles
        return []
