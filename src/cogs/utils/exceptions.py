class NotFound(Exception):
    pass


class GuildNotFound(NotFound):
    pass


class ChannelNotFound(NotFound):
    pass


class MemberNotFound(NotFound):
    pass


class MuteRoleNotFound(NotFound):
    pass


class MaximumRoles(Exception):
    pass


class PluginError(Exception):
    pass


class PluginDisabled(PluginError):
    pass


class NoMessage(PluginError):
    pass


class WrongGuild(Exception):
    pass
