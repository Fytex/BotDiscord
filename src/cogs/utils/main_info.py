from configparser import ConfigParser
from discord.ext import commands
from cogs.utils.exceptions import WrongGuild

PREMIUM_CH = 585638963683917845
UNBAN_CH = 585640026952564736

_ROLES_ = []
_CHANNELS_ = {}
parser = ConfigParser()
parser.read('settings.ini')

GUILD = parser.getint('Main', 'Guild_ID')
PREFIX = parser.get('Main', 'Prefix', fallback='!')
TOKEN = parser.get('Main', 'Token', fallback=None)

db_credentials = {}

for name in parser.options('Database'):
    db_credentials[name] = parser.get('Database', name)

for name in parser.options('Roles_IDs'):  # since ID is required
    role = {}
    role['name'] = name
    role['id'] = parser.getint('Roles_IDs', name)

    emoji = parser.get('Roles_Emojis', name, fallback=None)
    role['level'] = parser.getint('Roles_Levels', name, fallback=0)
    role['emoji'] = emoji and (r'\U000' + emoji).encode('UTF-8').decode('unicode-escape')
    _ROLES_.append(role)

for channel in parser.options('Channels_IDs'):
    _CHANNELS_[channel] = parser.getint('Channels_IDs', channel)


def _get_channel(client, ch_type):
    guild = client.get_guild(GUILD)
    channel = guild and guild.get_channel(_CHANNELS_.get(ch_type))
    return channel


def get_command_channel(client):
    return _get_channel(client, 'commands')


def get_servers_channel(client):
    return _get_channel(client, 'servers')


def get_status_channel(client):
    return _get_channel(client, 'status')


def get_moderation_channel(client):
    return _get_channel(client, 'moderation')


class IRoleObj:

    __slots__ = ('name', 'id', 'emoji', 'level')

    def __init__(self, role):
        self.name = role.get('name')
        self.id = role.get('id')
        self.emoji = role.get('emoji')
        self.level = role.get('level')


Iroles = [IRoleObj(role) for role in _ROLES_]

Iroles_find = {role.id: role for role in Iroles}


class UserInfo:
    def __init__(self, client, user):
        self.client = client
        self.user = user

    @property
    def guild(self):
        return self.client.get_guild(GUILD)

    @property
    def member(self):
        guild = self.guild
        return guild and guild.get_member(self.user.id)

    @property
    def iroles(self):
        if not self.member:
            return []
        member_roles_Roles = [role.id for role in self.member.roles]

        member_iroles = [Iroles_find[id] for id in member_roles_Roles if id in Iroles_find]

        return member_iroles

    @property
    def premium(self):
        return any(role.level == 1 for role in self.iroles)

    @property
    def mod(self):
        return any(role.level == 2 for role in self.iroles)

    @property
    def admin(self):
        return any(role.level == 3 for role in self.iroles) or self.mod

    @property
    def owner(self):
        return any(role.level == 4 for role in self.iroles) or self.admin


class MemberInfo(UserInfo):
    '''

    This is used for checking before and after member update (premium status!)

    '''

    def __init__(self, client, member):
        self._member = member
        super().__init__(client, member)
        if member.guild != self.guild:
            raise WrongGuild('Member\'s guild isn\'t the main one')

    @property
    def member(self):
        return self._member


def is_admin():
    async def predicate(ctx):
        user_info = UserInfo(ctx.bot, ctx.author)
        return user_info.admin
    return commands.check(predicate)


def is_owner():
    async def predicate(ctx):
        user_info = UserInfo(ctx.bot, ctx.author)
        return user_info.owner
    return commands.check(predicate)


def is_mod():
    async def predicate(ctx):
        user_info = UserInfo(ctx.bot, ctx.author)
        return user_info.mod
    return commands.check(predicate)


def is_premium():
    async def predicate(ctx):
        user_info = UserInfo(ctx.bot, ctx.author)
        return user_info.premium
    return commands.check(predicate)
