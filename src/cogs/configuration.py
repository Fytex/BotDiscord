import discord
from discord.ext import commands
from cogs.utils.mod import ModData
from cogs.utils.customdatas import *
from cogs.utils.rep import GuildRepData
from cogs.utils.time import SecondsConverter
from itertools import chain
from cogs.utils.main_info import UserInfo


def premium_guild():
    def predicate(ctx):
        admin_roles = [role for role in ctx.guild.roles if role.permissions.administrator]
        admin_members = {member for member in chain.from_iterable(
            [role.members for role in admin_roles])}

        return any(UserInfo(ctx.bot, user).premium for user in admin_members)
    return commands.check(predicate)


'''

Messages' title

'''


async def title(ctx, *, title):
    if len(title) >= 200:  # 256 limit
        return await ctx.dest.send('Número de caracteres excedido')

    title = title.replace('\n', '\\n')

    await ctx.dest.send(f'Título da mensagem de {ctx.fmt}s atualizada com sucesso!')

    await ctx.data.set_title(title)

'''

Messages' description

'''


async def description(ctx, *, description):
    if len(description) >= 2000:  # 2048 limit
        return await ctx.dest.send('Número de caracteres excedido')

    description = description.replace('\n', '\\n')

    await ctx.dest.send(f'Descrição da mensagem de {ctx.fmt} atualizada com sucesso!')

    await ctx.data.set_description(description)

'''

Messages' colour

'''


async def colour(ctx, colour=None):
    if colour is not None:
        colour_dict = {'vermelho': 'red', 'verde': 'green', 'azul': 'blue',
                       'laranja': 'orange', 'magenta': 'magenta', 'dourado': 'gold', 'roxo': 'purple'}

        colour = colour_dict.get(colour.lower())

        if colour is None:
            return await ctx.dest.send('Nenhuma cor disponível foi encontrada com esse nome.')

        await ctx.dest.send(f'A cor do embed da mensagem de {ctx.fmt} foi alterado com sucesso.')
    else:
        await ctx.dest.send(f'O embed da mensagem de {ctx.fmt} foi removido uma vez que removida a sua cor.')

    await ctx.data.set_colour(colour)

'''

Messages' destination

'''


async def channel(ctx, channel: discord.TextChannel = None):

    if channel is None and ctx.command.name == 'leave':
        return await ctx.dest.send('Não posso enviar mensagens ao utilizador quando sai do servidor.')

    if channel is None:
        await ctx.dest.send(f'Mensagens de {ctx.fmt} passarão a ser enviadas ao membro.')
    else:
        await ctx.dest.send(f'Canal de {ctx.fmt} alterado -> {channel.mention}')

    await ctx.data.set_channel(channel)

'''

Enable/Disable Welcome/Goodbye Message

'''


async def enable(ctx):
    if ctx.data.enabled:
        enabled = False
    else:
        enabled = True

    await ctx.data.set_enabled(enabled)
    fmt = 'ativada' if enabled else 'desativada'
    await ctx.dest.send(f'A mensagem de {ctx.fmt} foi {fmt}')


class LogsGroup(commands.Group):

    _all_cmds = (title, description, colour, channel, enable)

    _cmds_group_methods = {'mute': _all_cmds,
                           'kick': _all_cmds,
                           'ban': _all_cmds,
                           'avatar': (colour, channel, enable),
                           'rep': _all_cmds,
                           'join': _all_cmds,
                           'leave': _all_cmds,
                           'report': _all_cmds
                           }

    def add_command(self, command):

        super().add_command(command)

        cmds_methods = self._cmds_group_methods.get(command.name)

        if cmds_methods is None:
            return

        for cmd_method in cmds_methods:
            command.command()(cmd_method)

        self._cmds_group_methods.pop(command.name)


class Configuration(commands.Cog):

    def __init__(self, client):
        self.client = client

    async def cog_check(self, ctx):
        return ctx.guild is not None and ctx.author.guild_permissions.administrator

    async def cog_before_invoke(self, ctx):

        if ctx.command.parent:  # it will only execute once (subcommands won't pass here)
            return

        send_msg_perm = ctx.channel.permissions_for(ctx.me).send_messages
        ctx.dest = ctx.channel if send_msg_perm else ctx.author

    @commands.group()
    async def config(self, ctx):
        if ctx.invoked_subcommand is None:
            return await ctx.dest.send('Nenhum parâmetro encontrado...')

    @config.group(name='mod')
    async def mod_group(self, ctx):
        if ctx.invoked_subcommand is None:
            return await ctx.dest.send('Nenhum parâmetro dentro de `mod` encontrado...')
        ctx.mod_data = await ModData.get_Data(self.client, ctx.guild.id)

    @config.group(name='log', cls=LogsGroup)
    async def log_group(self, ctx):
        if ctx.invoked_subcommand is None:
            return await ctx.dest.send('Nenhum parâmetro dentro de `log` encontrado...')

    @config.group(name='rep')
    @premium_guild()
    async def rep_group(self, ctx):
        if ctx.invoked_subcommand is None:
            return await ctx.dest.send('Nenhum parâmetro dentro de `rep` encontrado...')
        ctx.rep_data = await GuildRepData.get_Data(self.client, ctx.guild.id)

    '''

    Mod

    '''

    @mod_group.command()
    async def mute_roles(self, ctx, roles: commands.Greedy[discord.Role]):

        await self._mod_roles(ctx, roles, 'mute')

    @mod_group.command()
    async def kick_roles(self, ctx, roles: commands.Greedy[discord.Role]):

        await self._mod_roles(ctx, roles, 'kick')

    @mod_group.command()
    async def ban_roles(self, ctx, roles: commands.Greedy[discord.Role]):

        await self._mod_roles(ctx, roles, 'ban')

    async def _mod_roles(self, ctx, roles, attr):

        translation = {'mute': 'silenciar', 'kick': 'expulsar', 'ban': 'banir'}

        fmt = translation.get(attr)

        if {role.id for role in roles} == ctx.mod_data.mute_roles:
            return await ctx.dest.send(f'Os cargos com acesso a {fmt} continuam iguais.')

        await getattr(ctx.mod_data, f'set_{attr}_roles')(roles)
        await ctx.dest.send('Os seguintes cargos foram adicionados com permissão de {}.\n`{}`'.format(fmt, '`, `'.join(map(str, roles))))

    '''


    Rep


    '''

    @rep_group.command()
    async def cooldown(self, ctx, time: SecondsConverter):
        if time <= 0 or time > 31536000:
            return await ctx.dest.send('Tempo tem de ser positivo e menor que um ano.')

        await ctx.rep_data.set_cooldown(time)
        await ctx.dest.send(f'Cooldown em segundos: `{time}s`')

    @rep_group.command()
    async def roles(self, ctx, roles: commands.Greedy[discord.Role]):

        if {role.id for role in roles} == ctx.rep_data.roles:
            return await ctx.dest.send(f'Os cargos com direito a reputação continuam iguais.')

        await ctx.rep_data.set_roles(roles)
        await ctx.dest.send('Os seguintes cargos foram adicionados com o direito a reputação.\n`{}`'.format('`, `'.join(map(str, roles))))

    '''


    Log



    '''

    @log_group.group()
    async def mute(self, ctx):

        if ctx.invoked_subcommand is None:
            return await ctx.dest.send('Nenhum parâmetro encontrado...')

        ctx.fmt = 'registro de silenciamentos'
        ctx.data = await MuteLogData.get_Data(self.client, ctx.guild.id)

    @log_group.group()
    async def kick(self, ctx):

        if ctx.invoked_subcommand is None:
            return await ctx.dest.send('Nenhum parâmetro encontrado...')

        ctx.fmt = 'registro de expulsões'
        ctx.data = await KickLogData.get_Data(self.client, ctx.guild.id)

    @log_group.group()
    async def ban(self, ctx):

        if ctx.invoked_subcommand is None:
            return await ctx.dest.send('Nenhum parâmetro encontrado...')

        ctx.fmt = 'registro de banimentos'
        ctx.data = await BanLogData.get_Data(self.client, ctx.guild.id)

    @log_group.group()
    async def avatar(self, ctx):

        if ctx.invoked_subcommand is None:
            return await ctx.dest.send('Nenhum parâmetro encontrado...')

        ctx.fmt = 'registro de avatar'
        ctx.data = await AvatarLogData.get_Data(self.client, ctx.guild.id)

    @log_group.group()
    async def rep(self, ctx):

        if ctx.invoked_subcommand is None:
            return await ctx.dest.send('Nenhum parâmetro encontrado...')

        ctx.fmt = 'registro de reputação'
        ctx.data = await RepLogData.get_Data(self.client, ctx.guild.id)

    @log_group.group()
    async def join(self, ctx):

        if ctx.invoked_subcommand is None:
            return await ctx.dest.send('Nenhum parâmetro encontrado...')

        ctx.fmt = 'boas-vindas'
        ctx.data = await WelcomeData.get_Data(self.client, ctx.guild.id)

    @log_group.group()
    async def leave(self, ctx):

        if ctx.invoked_subcommand is None:
            return await ctx.dest.send('Nenhum parâmetro encontrado...')

        ctx.fmt = 'despedida'
        ctx.data = await GoodbyeData.get_Data(self.client, ctx.guild.id)

    @log_group.group()
    @premium_guild()
    async def report(self, ctx):
        if ctx.invoked_subcommand is None:
            return await ctx.dest.send('Nenhum parâmetro encontrado...')

        ctx.fmt = 'denúncias'
        ctx.data = await ReportLogData.get_Data(self.client, ctx.guild.id)


def setup(client):
    client.add_cog(Configuration(client))
