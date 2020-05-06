from discord.ext import commands
from cogs.utils.timer import TimerData

import datetime
import cogs.utils.exceptions as exc
import asyncio


class Timer_Task(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.pending_unmutes = {}
        self.pending_unbans = {}
        self.skip_timestamp = None
        self._current_timer = None
        self._task = None

        self._task = self.run_task()

    @commands.Cog.listener()
    async def on_guild_role_update(self, before, after):
        guild = before.guild
        before_perms = before.guild.me.guild_permissions
        after_perms = after.guild.me.guild_permissions
        manage_roles_changed = not before_perms.manage_roles and after_perms.manage_roles
        ban_members_changed = not before_perms.ban_members and after_perms.ban_members

        if manage_roles_changed:

            pending_unmutes = self.pending_unmutes.get(guild.id)

            if pending_unmutes is not None:

                for timer_data in pending_unmutes[:]:
                    if await timer_data.bot_can_unmute():
                        await timer_data.unmute()
                    else:
                        await timer_data.remove_from_db()
                    pending_unmutes.remove(timer_data)

        if ban_members_changed:

            pending_unbans = self.pending_unbans.get(guild.id)

            if pending_unbans is not None:
                for timer_data in pending_unbans[:]:
                    await timer_data.unban()
                    pending_unmutes.remove(timer_data)

    async def task(self):

        await self.client.wait_until_ready()

        while not self.client.is_closed():

            try:

                if self._current_timer is None:
                    timer_data = await TimerData.get_Data(self.client, self.skip_timestamp)
                else:
                    # restarts the class without calling database (performance) returning a new class
                    timer_data = await timer_data.restart_TimerData()

            except (exc.MuteRoleNotFound, exc.GuildNotFound):
                await timer_data.remove_from_db()
            except exc.MemberNotFound:
                pass  # they can join later so we have to add the role back to him again


            if timer_data is None:
                return None

            self._current_timer = timer_data

            now = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)

            interval = (timer_data.time - now).total_seconds()

            if interval > 0:
                await asyncio.sleep(interval)
                continue  # after this time, bot/member could leave the server

            self._current_timer = None  # timer finishes

            if timer_data.event == 'mute':

                if not timer_data.guild.me.guild_permissions.manage_roles:  # we will unmute later if we don't have permission
                    # use a set because if we have to restart the task it will reset the skip_timestamp variable
                    self.pending_unmutes.setdefault(timer_data.guild.id, set()).add(timer_data)
                    self.skip_timestamp = timer_data.time
                    continue

                if await timer_data.bot_can_unmute():
                    await timer_data.unmute()

                else:
                    await timer_data.remove_from_db()

            if timer_data.event == 'ban':
                if not timer_data.guild.me.guild_permissions.ban_members:  # we will unban later if we don't have permission
                    # use a set because if we have to restart the task it will reset the skip_timestamp variable
                    self.pending_unbans.setdefault(timer_data.guild.id, set()).add(timer_data)
                    self.skip_timestamp = timer_data.time
                    continue
                await timer_data.unban()

    def run_task(self):

        if self._task is not None:
            self._current_timer = None
            self._task.cancel()

        return self.client.loop.create_task(self.task())


def setup(client):
    client.add_cog(Timer_Task(client))
