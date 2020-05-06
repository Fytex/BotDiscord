
from cogs.utils.data import Data


class WelcomeData(Data):

    db_table = 'welcome'

    def __init__(self, client, record):
        super().__init__(client, record)


class GoodbyeData(Data):
    db_table = 'goodbye'

    def __init__(self, client, record):
        super().__init__(client, record)


class MuteLogData(Data):
    db_table = 'mute_log'

    def __init__(self, client, record):
        super().__init__(client, record)


class KickLogData(Data):
    db_table = 'kick_log'

    def __init__(self, client, record):
        super().__init__(client, record)


class BanLogData(Data):
    db_table = 'ban_log'

    def __init__(self, client, record):
        super().__init__(client, record)


class RepLogData(Data):
    db_table = 'rep_log'

    def __init__(self, client, record):
        super().__init__(client, record)


class AvatarLogData(Data):
    db_table = 'avatar_log'

    def __init__(self, client, record):
        super().__init__(client, record)


class ReportLogData(Data):
    db_table = 'report_log'

    def __init__(self, client, record):
        super().__init__(client, record)

    @classmethod
    async def get_Data_From_Mutual_Guilds(cls, client, guilds):
        guilds_to_str = ', '.join(map(str, guilds))
        query = f'SELECT * FROM avatar_log WHERE guild IN ({guilds_to_str})'

        async with client.db.acquire() as con:
            records = await con.fetch(query)

        datas = [cls(client, record) for record in records]

        return datas
