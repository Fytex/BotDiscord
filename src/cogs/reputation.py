import discord
import datetime

from discord.ext import commands
from cogs.utils.rep import MemberRepData
from cogs.utils.time import get_string_time
import cogs.utils.exceptions as exc


class Reputation(commands.Cog):
    def __init__(self, client):
        self.client = client

    async def cog_check(self, ctx):
        return ctx.guild is not None

    async def cog_before_invoke(self, ctx):
        send_msg_perm = ctx.channel.permissions_for(ctx.me).send_messages
        ctx.dest = ctx.channel if send_msg_perm else ctx.author

    @commands.command()
    async def rep(self, ctx, member: discord.Member):

        if ctx.author == member or member.bot:
            return await ctx.dest.send('Não é permitido reputar a você mesmo nem a um bot.')

        try:
            data = await MemberRepData.get_Data(self.client, ctx.guild.id, member.id)
        except exc.PluginDisabled:
            return await ctx.dest.send('`Reputação` está desabilitada neste servidor pois não há nenhum cargo reputável')

        if not data.has_rep_role(member):
            return await ctx.dest.send(f'`{member}` não tem cargo de reputação.')

        now = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)

        if data.time and data.cooldown:
            min_time = data.time + datetime.timedelta(seconds=data.cooldown)

            if min_time > now:
                str_time = get_string_time(min_time)
                return await ctx.dest.send(f'Você está em coolown durante `{str_time}`')

        reps_count = await data.rep(member)

        await ctx.dest.send(f'Obrigado pelo seu voto de reputação a `{member}`')

        logs = self.client.get_cog('Logs')

        await logs.rep_log(member, ctx.author, reps_count)

    @commands.command()
    async def topreps(self, ctx):
        query = 'SELECT member, reps FROM rep_count WHERE guild=$1 ORDER BY reps DESC LIMIT 5'

        async with self.client.db.acquire() as con:
            record = await con.fetch(query, ctx.guild.id)

        top_reps = [f"{ctx.guild.get_member(row['member'])} -> {row['reps']} reputaç{'ões' if row['reps'] > 1 else 'ão'}"
                    for row in record]

        msg = '\n'.join(top_reps) if top_reps else 'Top Reps inexistente'
        await ctx.dest.send(msg)


def setup(client):
    client.add_cog(Reputation(client))
