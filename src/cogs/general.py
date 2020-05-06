import discord
from discord.ext import commands
from cogs.utils import main_info


class General(commands.Cog):

    def __init__(self, client):
        self.client = client

    async def cog_before_invoke(self, ctx):
        perms = ctx.channel.permissions_for(ctx.me)
        send_msg_perm = perms.send_messages
        ctx.to_embed = perms.embed_links or not send_msg_perm
        ctx.dest = ctx.channel if send_msg_perm else ctx.author

    @main_info.is_admin()
    @commands.command()
    async def show_guilds(self, ctx, page=0):
        guilds = self.client.guilds
        embed = None
        msg = []

        if len(guilds) < page*10:
            return await ctx.dest.send('Página inválida.')

        embed = discord.Embed(title='**Lista de Servidores**', description=str(ctx.me),
                              colour=discord.Colour.blurple())
        embed.set_thumbnail(url=ctx.me.avatar_url)

        for guild in guilds[page*10: page*10 + 10]:
            if ctx.to_embed:
                embed.add_field(name=guild.name, value=guild.id, inline=False)
            else:
                msg.append(f'{guild.name} -> {guild.id}')

        await ctx.dest.send('\n'.join(msg), embed=embed)

    @main_info.is_admin()
    @commands.command()
    async def remove_guild(self, ctx, id: int):
        guild = self.client.get_guild(id)
        if not guild:
            return await ctx.dest.send('Servidor não encontrado')
        await guild.leave()
        await ctx.dest.send(f'Saí do servidor {guild.name} como pedido')

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def colour(self, ctx, role: discord.Role, colour):
        not_author_perms = role >= ctx.author.top_role and ctx.author != ctx.guild.owner

        not_bot_perms = not ctx.me.guild_permissions.manage_roles or (
            role >= ctx.me.top_role and ctx.guild.me != ctx.guild.owner)

        if not_author_perms or not_bot_perms or role.is_default():
            return await ctx.dest.send(f'Um de nós não tem permissão para mudar a cor do seguinte cargo: `{role.name}`')

        colour = discord.Colour(int(colour, 16))
        await role.edit(colour=colour)
        await ctx.dest.send('Cor alterada com sucesso.')

    @main_info.is_premium()
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def set_prefix(self, ctx, new_prefix):
        prefixes = self.client.prefixes
        prefix = self.client.prefix
        old_prefix = prefixes.get(ctx.guild.id, prefix)

        if new_prefix == old_prefix:
            return await ctx.dest.send('O prefixo continua igual...')

        prefixes[ctx.guild.id] = new_prefix

        if new_prefix == prefix:
            return await self.remove_prefix(ctx)

        if old_prefix == prefix:
            query = 'INSERT INTO prefixes (guild, prefix) VALUES ($1, $2)'
        else:
            query = 'UPDATE prefixes SET prefix=$2 WHERE guild=$1'

        async with self.client.db.acquire() as con:
            await con.execute(query, ctx.guild.id, new_prefix)

        await ctx.dest.send(f'Prefixo alterado para `{new_prefix}`')

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def reset_prefix(self, ctx):
        prefixes = self.client.prefixes
        old_prefix = prefixes.get(ctx.guild.id)
        prefix = self.client.prefix

        if not old_prefix:
            return await ctx.dest.send(f'O prefixo de momento é o por defeito: `{prefix}`')

        await self.remove_prefix(ctx)

        await ctx.dest.send(f'Prefixo resetado com sucesso: `{prefix}`')

    async def remove_prefix(self, ctx):
        query = 'DELETE FROM prefixes WHERE guild=$1'
        async with self.client.db.acquire() as con:
            await con.execute(query, ctx.guild.id)

        self.client.prefixes.pop(ctx.guild.id)

    @main_info.is_mod()
    @commands.command()
    async def userban(self, ctx, *, raw_user):

        try:
            user = await commands.UserConverter().convert(ctx, raw_user)
        except commands.BadArgument:
            user = raw_user.isdigit() and await self.client.fetch_user(raw_user)

        if not user:
            return await ctx.dest.send('Não foi encontrado nenhum utilizador com os dados fornecidos')

        blacklist = self.client.blacklist

        if user.id in blacklist:
            return await ctx.dest.send(f'O utilizador `{user}` já se encontrava banido')

        blacklist.add(user.id)
        await ctx.dest.send(f'Utilizador `{user}` banido com sucesso. Ele não poderá usar mais os meus comandos')

        query = 'INSERT INTO user_blacklist (_user) VALUES ($1)'
        async with self.client.db.acquire() as con:
            await con.execute(query, user.id)

        cog = self.client.get_cog('MainLogs')
        await cog._blacklist_user_log(user, ctx.author)

    @main_info.is_admin()
    @commands.command()
    async def userunban(self, ctx, *, raw_user):

        try:
            user = await commands.UserConverter().convert(ctx, raw_user)
        except commands.BadArgument:
            user = raw_user.isdigit() and await self.client.fetch_user(raw_user)

        if not user:
            return await ctx.dest.send('Não foi encontrado nenhum utilizador com os dados fornecidos')

        try:
            self.client.blacklist.remove(user.id)
        except KeyError:
            await ctx.dest.send(f'O utilizador `{user}` não se encontrava banido.')
        else:
            await ctx.dest.send(f'Removi o banimento do utilizador `{user}`. Ele pode utilizar os meus comandos denovo')

            query = 'DELETE FROM user_blacklist WHERE _user=$1'
            async with self.client.db.acquire() as con:
                await con.execute(query, user.id)

            cog = self.client.get_cog('MainLogs')
            await cog._blacklist_user_log(user, ctx.author, ban=False)

    @main_info.is_mod()
    @commands.command()
    async def serverban(self, ctx, raw_guild: int):

        guild = self.client.get_guild(int(raw_guild))

        if guild:
            await guild.leave()
        else:
            try:
                guild = raw_guild and await self.client.fetch_guild(raw_guild)

            except discord.Forbidden:
                return await ctx.dest.send('Não foi encontrado nenhum utilizador com os dados fornecidos')

            query = 'SELECT guild FROM guild_blacklist WHERE guild=$1'
            async with self.client.db.acquire() as con:
                blacklisted = await con.fetchval(query, guild.id)

            if blacklisted:
                return await ctx.dest.send(f'O servidor `{guild.name}` já se encontrava proibído de usar o bot.')

        query = 'INSERT INTO guild_blacklist (guild) VALUES ($1)'
        async with self.client.db.acquire() as con:
            await con.execute(query, guild.id)

        await ctx.dest.send(f'Proibi o servidor ``{guild.name}` de usar o bot')

        cog = self.client.get_cog('MainLogs')
        await cog._blacklist_guild_log(guild, ctx.author)

    @main_info.is_admin()
    @commands.command()
    async def serverunban(self, ctx, raw_guild: int):

        guild = self.client.get_guild(int(raw_guild))
        if guild:
            return await ctx.dest.send(f'O servidor `{guild.name}` não se encontra proibído de usar o bot.')

        try:
            guild = raw_guild and await self.client.fetch_guild(raw_guild)
        except discord.Forbidden:
            return await ctx.dest.send('Não foi encontrado nenhum utilizador com os dados fornecidos')

        query = 'SELECT guild FROM guild_blacklist WHERE guild=$1'
        async with self.client.db.acquire() as con:
            blacklisted = await con.fetchval(query, guild.id)

        if not blacklisted:
            return await ctx.dest.send(f'O servidor `{guild.name}` não se encontra proibído de usar o bot.')

        query = 'DELETE FROM guild_blacklist WHERE guild=$1'
        async with self.client.db.acquire() as con:
            await con.execute(query, guild.id)

        await ctx.dest.send(f'O servidor ``{guild.name}` pode utilizar os meus comandos denovo!')

        cog = self.client.get_cog('MainLogs')
        await cog._blacklist_guild_log(guild, ctx.author, ban=False)

    @main_info.is_owner()
    @commands.command()
    async def restart(self, ctx):
        self.client.restart = True
        await ctx.dest.send('Irei reiniciar agora mesmo. Volto em segundos!')
        await self.client.logout()

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        query = 'SELECT guild FROM guild_blacklist WHERE guild=$1'
        async with self.client.db.acquire() as con:
            blacklisted = await con.fetchval(query, guild.id)

        if blacklisted:
            await guild.leave()


def setup(client):
    client.add_cog(General(client))
