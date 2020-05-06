class DB:
    def __init__(self, client):
        self.client = client

    @classmethod
    async def get_Data(cls, client, guild_id):
        query_fetch = f'SELECT * FROM {cls.db_table} WHERE guild=$1;'

        async with client.db.acquire() as con:
            record = await con.fetchrow(query_fetch, guild_id)

            if not record:  # if no record.... just create one
                query_insert = f'INSERT INTO {cls.db_table} (guild) VALUES ($1)'
                await con.execute(query_insert, guild_id)
                record = await con.fetchrow(query_fetch, guild_id)

        return cls(client, record)

    async def _send_to_db(self, column, value):

        '''
        Since each connections' query is simliar to the next one (Just change the column and the value to update)
        '''

        query = f'UPDATE {self.db_table} SET {column}=$1 WHERE guild=$2'

        async with self.client.db.acquire() as con:
            await con.execute(query, value, self.guild.id)

    async def _get_from_db(self, column):

        '''
        Since each connections' query is simliar to the next one (Just change the column to get the value)
        '''

        query = f'SELECT {column} FROM {self.db_table} WHERE guild=$2'

        async with self.client.db.acquire() as con:
            value = await con.fetchval(query, self.guild.id)

        return value
