import cogs.utils.exceptions as exc
from cogs.utils.mod import ModData


class TimerData(ModData):
    def __init__(self, client, record_timer, record_mod):
        self._args = (client, record_timer, record_mod)

        super().__init__(client, record_mod)

        self.member_id = member_id = record_timer['member']  # member_id for unban hack

        self.time = record_timer['time']

        self.event = record_timer['event']

        if self.event == 'mute':

            if self.mute_role is None:
                raise exc.MuteRoleNotFound('Role doesn\'t exist anymore')

            member = self.member = self.guild.get_member(member_id)
            if member is None:  # don't remove from db
                raise exc.MemberNotFound('Member not in guild but can rejoin with roles...')

    @classmethod
    async def get_Data(cls, client, last_timestamp=None):

        query_timer = 'SELECT * FROM timers ORDER BY time LIMIT 1;' if last_timestamp is None else 'SELECT * FROM timers WHERE time > $1 ORDER BY time LIMIT 1;'
        query_mod = '''SELECT * FROM config_mod WHERE guild=$1;'''

        async with client.db.acquire() as con:
            if last_timestamp is None:
                record_timer = await con.fetchrow(query_timer)
            else:
                record_timer = await con.fetchrow(query_timer, last_timestamp)

            if record_timer is None:
                return None

            guild_id = record_timer['guild']

            record_mod = await con.fetchrow(query_mod, guild_id)

        return cls(client, record_timer, record_mod)

    async def restart_TimerData(self):
        '''
        I want to get values from the instance and returns a new one similar
        '''
        return self.__class__(*self._args)

    async def unmute(self):

        return await super().unmute(self.member)

    async def unban(self):
        return await super().unban_by_id(self.member_id)

    async def remove_from_db(self):
        return await super().remove_time_from_db(id=self.member_id, event=self.event)

    async def bot_can_unmute(self):
        return self._bot_can_do_action(self.member)
