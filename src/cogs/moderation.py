import discord
from discord.ext import commands
from cogs.utils.mod import ModData
from cogs.utils.time import TimeConverter, get_string_time
import cogs.utils.exceptions as exc


class Moderation(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.msg_error = '''Can\'t {0} {1} because one of the following reasons:
        {1} has a higher or equal role has me or you
        You don\'t have any role allowed to use the command'''

    async def cog_check(self, ctx):
        return ctx.guild is not None

    async def cog_before_invoke(self, ctx):
        ctx.mod_data = await ModData.get_Data(self.client, ctx.guild.id)
        send_msg_perm = ctx.channel.permissions_for(ctx.me).send_messages
        ctx.dest = ctx.channel if send_msg_perm else ctx.author
        ctx.delete_time = 15 if send_msg_perm else None

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        mod_data = await ModData.get_Data(self.client, channel.guild.id)
        mod_data.set_one_channel_perms(channel)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if not member.guild.me.guild_permissions.manage_roles:
            return

        query = 'SELECT time from mute WHERE guild=$1 AND member=$2'

        async with self.client.db.acquire() as con:
            mute_time = await con.fetchrow(query, member.guild.id, member.id)

        if mute_time is None:
            return

        mod_data = await ModData.get_Data(self.client, member.guild.id)

        if mod_data.mute_role is None or not mod_data._bot_can_do_action(member):
            return

        await mod_data.mute(member)

    @commands.command()
    @commands.bot_has_permissions(ban_members=True)
    async def ban(self, ctx, target: discord.Member, time: TimeConverter = 0):
        mod_data = ctx.mod_data

        if not mod_data.can_ban(ctx.author, target):
            return await ctx.dest.send(self.msg_error.format('ban', target))

        if time is None:
            return await ctx.dest.send('Tempo não reconhecido ou não positivo')

        if time:

            string_time = get_string_time(time)
            fmt = f'durante {string_time}'
        else:
            fmt = string_time = 'permanentemente'

        await ctx.dest.send(f'`{target}` foi banido por {ctx.author} com sucesso {fmt}', delete_after=ctx.delete_time)

        await mod_data.ban(target, time)

    @commands.command()
    @commands.bot_has_permissions(kick_members=True)
    async def kick(self, ctx, target: discord.Member, reason=None):
        if not ctx.mod_data.can_kick(ctx.author, target):
            return await ctx.dest.send(self.msg_error.format('kick', target))

        logs = self.client.get_cog('logs')

        # check if a member was kicked by bot so it will log as kicked instead of left
        logs.kicked_members.setdefault(ctx.guild.id, {})[target.id] = ctx.author

        await target.kick()
        await ctx.dest.send(f'`{target}` foi expulso por {ctx.author} com sucesso', delete_after=ctx.delete_time)

    @commands.command()
    @commands.bot_has_permissions(manage_roles=True)
    async def mute(self, ctx, target: discord.Member, *, time: TimeConverter = 0):
        mod_data = ctx.mod_data

        if not mod_data.can_mute(ctx.author, target):
            return await ctx.dest.send(self.msg_error.format('mute', target))

        if time is None:
            return await ctx.dest.send('Tempo não reconhecido ou não positivo')

        if mod_data.mute_role is None:
            try:
                await mod_data.setup_mute_role()
            except exc.MaximumRoles:
                return await ctx.send('Alguma coisa deu errado....\n`Número de cargos tem de ser inferior ao limite máximo para poder criar o cargo Silenciado`')

        is_muted = await mod_data.is_muted(target)

        if is_muted:
            return await ctx.send('O membro já se encontrava silenciado...\nRemova o silêncio e volte a silenciar para escolher um novo intervalo de tempo.')

        if time:
            string_time = get_string_time(time)

            fmt = f'durante {string_time}'
        else:
            fmt = string_time = 'permanentemente'

        await ctx.dest.send(f'`{target}` foi silenciado por `{ctx.author}` {fmt} ', delete_after=ctx.delete_time)

        logs = self.client.get_cog('Logs')

        await logs.mute_log(target, ctx.author, string_time)

        await mod_data.mute(target, time)

    @commands.command()
    @commands.bot_has_permissions(manage_roles=True)
    async def unmute(self, ctx, target: discord.Member):
        mod_data = ctx.mod_data

        if mod_data.mute_role is None:  # se não tem mute role também não tem como o membro estar silenciado por este cargo
            return await ctx.dest.send('O membro não se encontra silenciado.')

        if not mod_data.can_mute(ctx.author, target):
            return await ctx.dest.send(self.msg_error.format('unmute', target))

        is_muted = await mod_data.is_muted(target)

        if not is_muted:
            return await ctx.send('O membro não se encontra silenciado.')

        await mod_data.unmute(target)
        await ctx.dest.send(f'Removi o silêncio a {target}', delete_after=ctx.delete_time)


def setup(client):
    client.add_cog(Moderation(client))
