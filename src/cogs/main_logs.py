import discord

from discord.ext import commands
from cogs.utils import main_info
from datetime import datetime
from cogs.utils.exceptions import WrongGuild


class MainLogs(commands.Cog):

    def __init__(self, client):
        self.client = client

    async def _log(self, channel, title, description, icon=None, colour=None):
        if not channel:
            return

        perms = channel.permissions_for(channel.guild.me)

        if not perms.send_messages:
            return

        msg = None
        embed = None

        if perms.embed_links:
            embed = discord.Embed(title=title, description=description,
                                  colour=colour, timestamp=datetime.utcnow())
            embed.set_thumbnail(url=icon)
        else:
            msg = f'**{title}**\n\n{description}'

        await channel.send(msg, embed=embed)

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        params = {'channel': main_info.get_servers_channel(self.client),
                  'title': 'Servidores',
                  'description': f'Entrei no servidor: {guild.name}\nID: {guild.id}',
                  'colour': discord.Colour.green(),
                  'icon': guild.icon_url}
        await self._log(**params)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        params = {'channel': main_info.get_servers_channel(self.client),
                  'title': 'Servidores',
                  'description':  f'Saí no servidor: {guild.name}\nID: {guild.id}',
                  'colour': discord.Colour.red(),
                  'icon': guild.icon_url}
        await self._log(**params)

    async def _commands_log(self, ctx):
        params = {'channel': main_info.get_command_channel(self.client),
                  'title': 'Commando',
                  'description':  f'Autor: {ctx.author}\nServidor: {ctx.guild.name}\n\n{ctx.message.content}',
                  'colour': discord.Colour.blurple(),
                  'icon': ctx.author.avatar_url}
        await self._log(**params)

    async def _blacklist_user_log(self, user, author, ban=True):
        if ban:
            description = f'Utilizador `{user}` foi proibido de utilizar o bot\nAção executada por {author}'
            colour = discord.Colour.red()
        else:
            description = f'Utilizador `{user}` recebeu a permissão de utilizar o bot\nAção executada por {author}'
            colour = discord.Colour.green()
        params = {'channel': main_info.get_moderation_channel(self.client),
                  'title': 'Banimentos do BOT',
                  'description': description,
                  'colour': colour,
                  'icon': user.avatar_url}
        await self._log(**params)

    async def _blacklist_guild_log(self, guild, author, ban=True):
        if ban:
            description = f'Servidor `{guild}` foi proibido de utilizar o bot\nAção executada por {author}'
            colour = discord.Colour.red()
        else:
            description = f'Servidor `{guild}` recebeu a permissão de utilizar o bot\nAção executada por {author}'
            colour = discord.Colour.green()
        params = {'channel': main_info.get_moderation_channel(self.client),
                  'title': 'Banimentos do BOT',
                  'description': description,
                  'colour': colour,
                  'icon': guild.icon_url}
        await self._log(**params)

    @commands.Cog.listener()
    async def on_ready(self):
        params = {'channel': main_info.get_status_channel(self.client),
                  'title': 'Estado',
                  'description':  f'Estou online!',
                  'colour': discord.Colour.gold(),
                  'icon': self.client.user.avatar_url}
        await self._log(**params)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):

        if before.roles == after.roles:
            return

        try:
            premium_before = main_info.MemberInfo(self.client, before).premium
            premium_after = main_info.MemberInfo(self.client, after).premium
        except WrongGuild:
            return

        if premium_before == premium_after:
            return

        params = {'channel': main_info.get_moderation_channel(self.client),
                  'title': 'Premium',
                  'description':  f'O utilizador `{after}` ganhou acesso premium' if premium_after else f'O utilizador `{after}` perdeu acesso premium',
                  'colour': discord.Colour.blue() if premium_after else discord.Colour.orange(),
                  'icon': after.avatar_url}

        await self._log(**params)


def setup(client):
    client.add_cog(MainLogs(client))
