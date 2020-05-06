import discord
from discord.ext import commands
from cogs.utils.customdatas import ReportLogData
from cogs.utils.main_info import UserInfo
from itertools import chain


class Report(commands.Cog):

    def __init__(self, client):
        self.client = client

    async def cog_check(self, ctx):
        if not ctx.guild:
            return False
        admin_roles = [role for role in ctx.guild.roles if role.permissions.administrator]
        admin_members = {member for member in chain.from_iterable(
            [role.members for role in admin_roles])}

        return any(UserInfo(ctx.bot, user).premium for user in admin_members)

    async def cog_before_invoke(self, ctx):
        ctx.report_data = None
        send_msg_perm = ctx.channel.permissions_for(ctx.me).send_messages
        ctx.dest = ctx.channel if send_msg_perm else ctx.author

    @commands.command()
    async def report(self, ctx, member: discord.Member, *, reason):

        data = await ReportLogData.get_Data(self.client, ctx.guild.id)

        if not data.enabled or not data.description or not data.channel:
            return await ctx.dest.send('`Denúncias` está desativado neste servidor')

        if member == ctx.author:
            return await ctx.dest.send('Você não se pode denunciar a si próprio')

        logs = self.client.get_cog('Logs')

        await logs.report_log(member, ctx.author, reason, data=data)
        await ctx.author.send(f'**Denúncia**\n```Membro: {member}\nMotivo: {reason}```')


def setup(client):
    client.add_cog(Report(client))
