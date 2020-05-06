import asyncpg
import discord
import os
from discord.ext import commands
from cogs.utils.main_info import get_command_channel
from cogs.utils.main_info import PREFIX, TOKEN, db_credentials

extensions = ['moderation', 'timer_task', 'configuration',
              'logs', 'info', 'reputation', 'report', 'general', 'main_logs']


async def bot_db_startup(client):
    query_prefixes = 'SELECT * FROM prefixes'
    query_user_blacklist = 'SELECT * FROM user_blacklist'
    query_guild_blacklist = 'SELECT * FROM guild_blacklist'
    async with client.db.acquire() as con:
        record_prefixes = await con.fetch(query_prefixes)
        record_user_blacklist = await con.fetch(query_user_blacklist)
        record_guild_blacklist = await con.fetch(query_guild_blacklist)

    client.prefixes = {row['guild']: row['prefix'] for row in record_prefixes}
    client.blacklist = {row['_user'] for row in record_user_blacklist}
    client.record_guild_blacklist = record_guild_blacklist


def get_prefix(client, message):
    return client.prefixes.get(message.guild.id, client.prefix)


class Bot(commands.AutoShardedBot):

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.prefix = PREFIX  # default

        self.restart = False

        self.db = self.loop.run_until_complete(asyncpg.create_pool(**db_credentials))

        self.loop.run_until_complete(bot_db_startup(self))


client = Bot(command_prefix=get_prefix, case_insensitive=True)


@client.event
async def on_ready():

    for row in client.record_guild_blacklist:
        guild = client.get_guild(row['guild'])
        if guild:
            await guild.leave()

    del client.record_guild_blacklist

    with open('art_h43.txt', 'r') as file:
        image = file.read()

    print(image)


@client.after_invoke
async def after_invoke(ctx):
    if not client.is_closed():  # restarts doesn't pass here
        cog = client.get_cog('MainLogs')
        await cog._commands_log(ctx)


@client.check_once
async def bot_check_once(ctx):
    return ctx.author.id not in client.blacklist


if __name__ == "__main__":
    for extension in extensions:
        client.load_extension('cogs.' + extension)
        '''
        try:
            client.load_extension(extension)
            print(f"Extension executed: {extension}")
        except Exception as error:
            print(f"The extension {extension} failed. Error = {error}")
        '''

    client.run(TOKEN)

    if client.restart:
        os.system('main.py')
