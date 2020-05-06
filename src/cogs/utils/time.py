import re
import datetime
from discord.ext import commands


class TimeConverter(commands.Converter):

    async def convert(self, ctx, argument):

        if not argument:  # forever
            return 0

        time_regex = re.compile(r'(?:([0-9]{1,5})\s?(d|h|m))+?')
        time_dict = {"d": 1440, "h": 60, "m": 1}

        args = argument.lower()

        matches = re.findall(time_regex, args)

        minutes = sum(time_dict[v]*int(k) for k, v in matches)

        if not minutes:  # not found
            return None

        now_ts = datetime.datetime.utcnow().replace(
            tzinfo=datetime.timezone.utc)

        future_ts = now_ts + datetime.timedelta(minutes=minutes)

        return future_ts


class SecondsConverter(commands.Converter):

    async def convert(self, ctx, argument):

        if not argument:  # forever
            return 0

        time_regex = re.compile(r'(?:([0-9]{1,5})\s?(d|h|m|s))+?')
        time_dict = {"d": 86400, "h": 3600, "m": 60, 's': 1}

        args = argument.lower()

        matches = re.findall(time_regex, args)

        seconds = sum(time_dict[v]*int(k) for k, v in matches)

        return seconds


'''

Return timestamp in future


'''


def get_string_time(time):

    now = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
    total_seconds = int((time - now).total_seconds())
    days, remaining = divmod(total_seconds, 60*60*24)
    hours, remaining = divmod(remaining, 60*60)
    minutes, seconds = divmod(remaining, 60)
    time_dict = {'d': days, 'h': hours, 'm': minutes, 's': seconds}
    time_list = [f'{v}{k}' for k, v in time_dict.items() if v]
    return ' '.join(time_list)
