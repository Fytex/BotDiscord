import discord

from discord.ext import commands
from cogs.utils.main_info import UserInfo


class Info(commands.Cog):

    def __init__(self, client):
        self.client = client

    def cog_check(self, ctx):
        if ctx.guild is None:
            return False
        return True

    async def cog_before_invoke(self, ctx):
        perms = ctx.channel.permissions_for(ctx.me)
        send_msg_perm = perms.send_messages
        ctx.to_embed = perms.embed_links or not send_msg_perm
        ctx.dest = ctx.channel if send_msg_perm else ctx.author

    @commands.command()
    async def serverinfo(self, ctx):
        members = len(ctx.guild.members)
        bots = sum(1 for member in ctx.guild.members if member.bot)
        humans = members - bots
        embed = None
        msg = ''

        fields = (('🔖 -> Nome', ctx.guild.name),
                  ('👑-> Dono', ctx.guild.owner),
                  ('👥-> Membros', len(ctx.guild.members)),
                  ('🤖-> Robôs', bots),
                  ('👨-> Humanos', humans),
                  ('😁-> Emojis', len(ctx.guild.emojis)),
                  ('🕤 -> Criado em', ctx.guild.created_at.strftime('%d %b %Y às %H:%M')),
                  ('🌎 -> Região', str(ctx.guild.region).title())
                  )
        if ctx.to_embed:
            embed = discord.Embed(colour=discord.Colour.gold(), title='**Informações do Servidor **',
                                  timestamp=ctx.message.created_at)
            embed.set_thumbnail(url=ctx.guild.icon_url)

            for name, value in fields:
                embed.add_field(name=name, value=value)

            embed.set_footer(text='Executado por: {}'.format(
                ctx.author), icon_url=ctx.author.avatar_url)
        else:
            _list = []

            for name, value in fields:
                _list.append(f'**{name}** -> {value}')

            msg = '\n'.join(_list)

        await ctx.dest.send(msg, embed=embed)

    @commands.command()
    async def info(self, ctx, member: discord.Member = None):

        member = member or ctx.author
        user_info = UserInfo(self.client, member)
        embed = None
        msg = ''
        Status = discord.Status
        status_translation = {
            Status.online: 'Online',
            Status.offline: 'Offline',
            Status.idle: 'Ausente',
            Status.dnd: 'Ocupado',
        }

        ActivityType = discord.ActivityType
        type_translation = {
            ActivityType.unknown: 'Desconhecido',
            ActivityType.playing: 'Jogando',
            ActivityType.streaming: 'Transmitindo',
            ActivityType.listening: 'Ouvindo',
            ActivityType.watching: 'Visualizando'
        }

        activity = (member.activity and member.activity.name) or 'Nada'
        activity_type = (member.activity and type_translation.get(
            member.activity.type)) or 'Fazendo'

        # alguns cargos podem ter os mesmos emojis
        emojis = {role.emoji for role in user_info.iroles if role.emoji}

        fields = (('🔖-> Nome', member.name),
                  ('😄 -> Emojis', 'Nenhum' if not emojis else ''.join(emojis)),
                  ('🏷️-> Tag', member.discriminator),
                  ('📋 -> Nick', member.display_name),
                  ('🆔-> ID', member.id),
                  ('👀-> Estado', status_translation.get(member.status)),
                  (f'💤-> {activity_type.capitalize()}', activity),
                  ('📄-> Cargo Maior', member.top_role),
                  ('⌛ -> Entrou',  member.joined_at.strftime('%d %b %Y às %H:%M')),
                  ('🕤 -> Criado', member.created_at.strftime('%d %b %Y às %H:%M')),
                  )

        if ctx.to_embed:
            embed = discord.Embed(title=f"**Informações do Utilizador**",
                                  colour=discord.Colour.blue(), timestamp=ctx.message.created_at)
            embed.set_thumbnail(url=member.avatar_url)

            for name, value in fields:
                embed.add_field(name=name, value=value)

            embed.set_footer(text='Executado por: {}'.format(
                ctx.author), icon_url=ctx.author.avatar_url)

        else:
            _list = []

            for name, value in fields:
                _list.append(f'**{name}** -> {value}')

            msg = '\n'.join(_list)

        await ctx.dest.send(msg, embed=embed)


def setup(client):
    client.add_cog(Info(client))
