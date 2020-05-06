import datetime
import cogs.utils.exceptions as exc
from cogs.utils.database import DB


class GuildRepData(DB):

    db_table = 'config_rep'

    def __init__(self, client, record):
        super().__init__(client)

        roles = record['roles']
        guild_id = record['guild']
        self.cooldown = record['cooldown']

        # this is just used by the guild so there is no need to check
        self.guild = client.get_guild(guild_id)
        self.roles = set(roles) if roles is not None else set()

    def has_rep_role(self, member):
        return any(role.id in self.roles for role in member.roles)

    async def set_cooldown(self, time):
        await self._send_to_db('cooldown', time)

    async def set_roles(self, roles):
        roles = [role.id for role in roles]
        await self._send_to_db('roles', roles)


class MemberRepData(GuildRepData):

    def __init__(self, client, record_config, record_cooldown):
        super().__init__(client, record_config)

        # this is just used by the member so there is no need to check
        self.time = record_cooldown and record_cooldown['time']

    @property
    def member(self):
        return self.guild.get_member(self.member_id)

    @classmethod
    async def get_Data(cls, client, guild_id, member_id):

        # this will take member_id as a parameter since it searches for the member

        query_config = 'SELECT * FROM config_rep WHERE guild=$1'
        query_cooldown = 'SELECT * FROM rep_cooldown WHERE guild=$1 AND member=$2'

        async with client.db.acquire() as con:
            record_config = await con.fetchrow(query_config, guild_id)
            record_cooldown = await con.fetchrow(query_cooldown, guild_id, member_id)

        if not record_config:
            raise exc.PluginDisabled('Reputation Plugin is not enabled in this server')

        data_cls = cls(client, record_config, record_cooldown)
        data_cls.member_id = member_id  # if no row is found at least we got member

        return data_cls

    async def rep(self, member):
        if self.time:
            query_time = 'UPDATE rep_cooldown SET time=$3 WHERE guild=$1 AND member=$2'
        else:
            query_time = 'INSERT INTO rep_cooldown (guild, member, time) VALUES ($1, $2, $3)'
        query_get_count = 'SELECT reps FROM rep_count WHERE guild=$1 AND member=$2'
        query_create_count = 'INSERT INTO rep_count (guild, member, reps) VALUES ($1, $2, $3)'
        query_update_count = 'UPDATE rep_count SET reps=$3 WHERE guild=$1 AND member=$2'

        now_ts = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)

        async with self.client.db.acquire() as con:
            await con.execute(query_time, self.guild.id, self.member.id, now_ts)
            reps_count = await con.fetchval(query_get_count, self.guild.id, member.id)

            if reps_count is None:
                await con.execute(query_create_count, self.guild.id, member.id, 1)
            else:
                await con.execute(query_update_count, self.guild.id, member.id, reps_count + 1)

        return (reps_count and reps_count + 1) or 1
