import discord
import re

from discord.ext import commands
from cogs.utils.customdatas import *
from functools import wraps
from datetime import datetime


class Logs(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.kicked_members = {}

    async def cog_check(self, ctx):
        return ctx.guild is not None

    def _before_member_events(func):

        @wraps(func)
        async def wrapper(self, member):

            if func.__name__ == 'on_member_join':
                data = await WelcomeData.get_Data(self.client, member.guild.id)
            elif func.__name__ == 'on_member_remove':

                guild_id = member.guild.id
                author = None

                try:
                    author = self.kicked_members.get(guild_id, {}).pop(member.id)
                except KeyError:
                    was_kicked = False
                else:
                    was_kicked = True

                if was_kicked:
                    data = await KickLogData.get_Data(self.client, guild_id)
                else:
                    data = await GoodbyeData.get_Data(self.client, guild_id)
            else:
                return

            await func(self, member, data, author)
        return wrapper

    @commands.Cog.listener()
    @_before_member_events
    async def on_member_join(self, member, data, author):

        await self._send_msg(data, member=member, can_dms=True, author=author)

    @commands.Cog.listener()
    @_before_member_events
    async def on_member_remove(self, member, data, author):

        await self._send_msg(data, member=member, can_dms=False, author=author)

    async def _send_msg(self, data, member=None, user=None, guild=None, can_dms=False, mute_time=None, author=None,  reps_count=None, report_text=None):
        channel = data.channel
        colour = data.colour
        embed = bool(colour)
        embed_msg = None
        msg = None
        guild = guild or member.guild
        member = user or member

        if not data.description or not data.enabled:
            return

        if channel is not None:

            perms = channel.permissions_for(guild.me)

            if not perms.send_messages:
                return

            if not perms.embed_links:
                embed = False

            dest = channel

        else:

            if not can_dms:
                return

            dest = member

        def replace_all(string):
            if string is not None:
                atm_time = datetime.now().strftime('%d/%m/%Y, %H %M')

                replacements = {'\\n': '\n',
                                '{membro}': member,
                                '{membro|menção}': member.mention,
                                '{membro|id}': member.id,
                                '{servidor}': guild.name,
                                '{membro|nome}': member.name,
                                '{tempo|atual}': atm_time,
                                '{tempo|estimado}': mute_time,
                                '{autor}': author,
                                '{autor|nome}': author and author.name,
                                '{autor|menção}': author and author.mention,
                                '{autor|id}': author and author.id,
                                '{reputações}': reps_count,
                                '{denúncia}': report_text}

                rep = dict((re.escape(k), str(v)) for k, v in replacements.items())
                pattern = re.compile("|".join(rep.keys()))
                string = pattern.sub(lambda m: rep[re.escape(m.group(0))], string)

            return string

        title = replace_all(data.title)
        description = replace_all(data.description)

        if embed:
            embed_msg = discord.Embed(title=title, description=description,
                                      colour=getattr(discord.Colour, colour)())
            embed_msg.set_thumbnail(url=member.avatar_url)
        else:
            title = f'**{title}**\n\n' if title else ''
            msg = f'{title}{description}'

        await dest.send(msg, embed=embed_msg)

    @commands.Cog.listener()
    async def on_user_update(self, before_user, after_user):
        client = self.client
        if before_user.avatar == after_user.avatar:
            return

        mutual_guilds_ids = [
            guild.id for guild in client.guilds if guild.get_member(after_user.id) is not None]
        avatar_datas_list = await AvatarLogData.get_Data_From_Mutual_Guilds(client, mutual_guilds_ids)

        for avatar_data in avatar_datas_list:

            if not avatar_data.enabled:
                continue

            channel = avatar_data.channel

            perms = channel and channel.permissions_for(channel.guild.me)

            if perms is None or not perms.send_messages or not perms.embed_links:
                continue

            colour = avatar_data.colour

            if colour is not None:
                colour = getattr(discord.Colour, colour)()

            embed = discord.Embed(title=str(after_user),
                                  description='➡️➡️ **Antiga** ➡️➡️', colour=colour)
            embed.add_field(name='-'*20, value='⬇️⬇️ **Nova** ⬇️⬇️')
            embed.set_thumbnail(url=before_user.avatar_url)
            embed.set_image(url=after_user.avatar_url)

            await avatar_data.channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        data = await BanLogData.get_Data(self.client, guild.id)

        await self._send_msg(data, guild=guild, user=user, can_dms=False)

    async def mute_log(self, member, author, time):
        data = await MuteLogData.get_Data(self.client, member.guild.id)
        await self._send_msg(data, member=member, author=author, can_dms=False, mute_time=time)

    async def rep_log(self, member, author, reps_count):
        data = await RepLogData.get_Data(self.client, member.guild.id)
        await self._send_msg(data, member=member, author=author, can_dms=False,  reps_count=reps_count)

    async def report_log(self, member, author, text, data=None):
        data = data or await ReportLogData.get_Data(self.client, member.guild.id)
        await self._send_msg(data, member=member, author=author, can_dms=False,  report_text=text)


def setup(client):
    client.add_cog(Logs(client))
