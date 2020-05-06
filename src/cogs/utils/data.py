from cogs.utils.database import DB


class Data(DB):
    def __init__(self, client, record):
        super().__init__(client)
        self.enabled = record['enabled']
        self.colour = record['colour']  # if no colour then it wont embed
        try:  # avatar doesn't have title neither description
            self.title = record['title']
            self.description = record['description']
        except KeyError:
            pass

        channel_id = record['channel']
        guild_id = record['guild']

        self.guild = guild = client.get_guild(guild_id)

        self.channel = channel_id and guild.get_channel(channel_id)

    async def set_enabled(self, enabled: bool):
        self.enabled = enabled
        await self._send_to_db('enabled', enabled)

    async def set_channel(self, channel):
        self.channel = channel
        await self._send_to_db('channel', channel.id)

    async def set_colour(self, colour):
        self.colour = colour
        await self._send_to_db('colour', colour)

    async def set_title(self, title):
        self.title = title
        await self._send_to_db('title', title)

    async def set_description(self, description):
        self.description = description
        await self._send_to_db('description', description)
