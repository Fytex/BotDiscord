import discord
import asyncio
import cogs.utils.exceptions as exc
from cogs.utils.database import DB


class ModData(DB):

    db_table = 'config_mod'

    def __init__(self, client, record):
        super().__init__(client)

        ban_roles = record['ban_roles']
        kick_roles = record['kick_roles']
        mute_roles = record['mute_roles']

        self.ban_roles = set(ban_roles) if ban_roles else set()
        self.kick_roles = set(kick_roles) if kick_roles else set()
        self.mute_roles = set(mute_roles) if mute_roles else set()

        guild_id = record['guild']
        self.guild = guild = guild_id and client.get_guild(guild_id)
        if guild is None:
            raise exc.GuildNotFound('Given ID wasn\'t a valid one')

        mute_role_id = record['mute_role']
        self.mute_role = mute_role_id and self.guild.get_role(mute_role_id)

        log_channel_id = record['log_channel']
        self.log_channel = log_channel_id and self.guild.get_channel(log_channel_id)

    def bot_can_log(self):
        channel = self.log_channel
        if not channel:
            return False

        bot_perms = channel.permissions_for(self.guild.me)
        if not bot_perms.send_messages or not bot_perms.embed_links:
            return False
        return True

    def _user_can_do_action(self, user, target):
        guild_owner = self.guild.owner
        return (user.top_role > target.top_role and target != guild_owner) or user == guild_owner

    def _bot_can_do_action(self, target):
        bot = self.guild.me
        guild_owner = self.guild.owner
        return (bot.top_role > target.top_role and target != guild_owner) or bot == guild_owner

    def can_mute(self, user, target):  # can a member mute another member?
        if not self._user_can_do_action(user, target) or not self._bot_can_do_action(target):
            return False
        return user.guild_permissions.administrator or any(role.id in self.mute_roles for role in user.roles)

    def can_kick(self, user, target):  # can a member kick another member?
        if not self._user_can_do_action(user, target) or not self._bot_can_do_action(target):
            return False
        return user.guild_permissions.administrator or any(role.id in self.kick_roles for role in user.roles)

    def can_ban(self, user, target):  # can a member ban another member?
        if not self._user_can_do_action(user, target) or not self._bot_can_do_action(target):
            return False
        return user.guild_permissions.administrator or any(role.id in self.ban_roles for role in user.roles)

    async def is_muted(self, target):
        return any(role == self.mute_role for role in target.roles)

    async def mute(self, target, time):

        await target.add_roles(self.mute_role)
        if time:
            await self._add_time_to_db(target, time, 'mute')

    async def ban(self, target, time):
        await target.ban()
        await self._add_time_to_db(target, time, 'ban')

    async def _add_time_to_db(self, target, time, event):

        if time is not None:  # if not time then its forever
            query_insert = 'INSERT INTO timers (guild, member, time, event) VALUES ($1, $2, $3, $4)'

            async with self.client.db.acquire() as con:
                await con.execute(query_insert, self.guild.id, target.id, time, event)

            mute_task_cog = self.client.get_cog('Mute_Task')

            if mute_task_cog._task.done() or mute_task_cog._current_timer.time > time:
                await mute_task_cog.run_task()

    async def unmute(self, target):

        await target.remove_roles(self.mute_role)
        await self.remove_time_from_db(target, event='mute')
        

    async def remove_time_from_db(self, target=None, id=None, event=None):
        id = id or target.id
        '''

        Removing row from database only (Mute_Task if no mute_role)

        '''
        query_delete = 'DELETE FROM timers WHERE guild=$1 AND member=$2 AND event=$3'

        async with self.client.db.acquire() as con:
            await con.execute(query_delete, self.guild.id, id, event)

    async def setup_mute_role(self):

        if len(self.guild.roles) == 250:
            raise exc.MaximumRoles('250 roles limit.')

        mute_role = await self.guild.create_role(name='Silenciado', colour=discord.Colour.dark_grey())
        self.mute_role = mute_role

        await self._send_to_db('mute_role', mute_role.id)

        await self.set_channels_perms()

        return mute_role

    async def set_channels_perms(self):
        tasks = []
        for channel in self.guild.text_channels:
            task = asyncio.ensure_future(self.set_one_channel_perms(channel))
            tasks.append(task)

        await asyncio.wait(tasks)

    async def set_one_channel_perms(self, channel):
        bot = self.guild.me
        perms = channel.permissions_for(bot)
        if perms.manage_roles:
            try:
                await channel.set_permissions(self.mute_role, send_messages=False, add_reactions=False)
            except discord.HTTPException:
                pass

    async def set_mute_roles(self, roles):
        roles = [role.id for role in roles]
        await self._send_to_db('mute_roles', roles)

    async def set_kick_roles(self, roles):
        roles = [role.id for role in roles]
        await self._send_to_db('kick_roles', roles)

    async def set_ban_roles(self, roles):
        roles = [role.id for role in roles]
        await self._send_to_db('ban_roles', roles)

    async def unban_by_id(self, id):
        user = discord.Object(id=id)
        try:
            await self.guild.unban(user)
        except discord.NotFound:
            pass
        finally:
            await self.remove_time_from_db(id=id, event='ban')
