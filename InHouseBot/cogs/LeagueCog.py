import discord
import httpx
from functools import wraps
import gspread

from discord.ext import commands

SHEET_NUM_IDX = 1
SHEET_NAME_IDX = 2
SHEET_ID_IDX = 3
SHEET_URL_IDX = 4

# Using this later for our reauth
def retry_authorize(exceptions, tries=4):
    def deco_retry(f):
        @wraps(f)
        async def f_retry(*args, **kwargs):
            mtries = tries
            while mtries > 1:
                try:
                    return await f(*args, **kwargs)
                except exceptions as e:
                    msg = f"{e}, Reauthorizing and retrying ..."
                    gspread.login()
                    print(msg)
                    mtries -= 1
            return await f(*args, **kwargs)

        return f_retry  # true decorator

    return deco_retry


class LeagueCog(commands.Cog):
    def __init__(self, bot, creds):

        self.creds = creds
        self._init_sheet()
        
        self.client = httpx.AsyncClient()
    
        # break is a keyword so we can't define it on class, interesting
        self.broke = False

    def _init_sheet(self):
        self.clients = gspread.authorize(self.creds)
        self.sheet = self.clients.open("InHouseData").sheet1

        # Lets cache on init
        self.cache = self.sheet.get_all_values()
        # data = self.sheet.get_all_records()

    @commands.command()
    @retry_authorize(gspread.exceptions.APIError)
    async def addstream(self, ctx, url=""):
        """ Configure your stream to our database! """
        user = ctx.message.author

        # If user exists, just update stream and exit
        # We can cache since if we add a new user, we update anyways
        for idx, row in enumerate(self.cache):
            if row[2] == str(user.id):
                self.sheet.update_cell(idx + 1, SHEET_URL_IDX, url)
                # Update our cache
                row[3] = url

                return

        # Otherwise add an entire new row for the user
        userlist = [len(self.cache), user.name, str(user.id), url]
        self.sheet.append_row(userlist)

        # Update cache
        self.cache.append(userlist)

    @commands.command()
    @retry_authorize(gspread.exceptions.APIError)
    async def stream(self, ctx):
        """ Post your own stream """
        user = ctx.message.author
        for row in self.cache:
            # We are not using SHEET_* constants becuase this is a python array
            # representation of the data, not indexing remotely
            if row[2] == str(user.id):
                msg = row[3]
                return await ctx.send(msg)

        # User not found
        await ctx.send(
            "You do not have any stream set up yet. Use !addstream to configure."
        )

    @commands.command()
    @retry_authorize(gspread.exceptions.APIError)
    async def streams(self, ctx):
        """ Show list of streams """
        max_name_len = max([len(x[1]) for x in self.cache[1:]])

        # We are not using SHEET_* constants becuase this is a python array
        # representation of the data, not indexing remotely
        msg = "".join(
            [
                "{0: <{pad}} :\t{1}\n".format(row[1], row[3], pad=max_name_len)
                for row in self.cache[1:]
            ]
        )
        await ctx.send(msg)

    @commands.command(
        name="break"
    )  # remember, its keyworded so we can't define it as is
    async def _break(self, ctx):
        """ Generates a prodraft lobby and records blue/red team memebers """

        blue_channel = discord.utils.get(
            ctx.guild.channels, name="Blue Team 1", type=discord.ChannelType.voice
        )
        red_channel = discord.utils.get(
            ctx.guild.channels, name="Red Team 2", type=discord.ChannelType.voice
        )

        # We don't have to intialize these since they are only in scope if we
        # invoke this command

        self.blue_team = blue_channel.members
        self.red_team = red_channel.members

        # Lets do some fun custom team names :)

        draft_lobby_req = await self.client.post(
            "http://prodraft.leagueoflegends.com/draft",
            json={
                "team1Name": "Blue Side",
                "team2Name": "Red Side",
                "matchName": "Inhouse Lobby",
            },
        )

        draft_lobby_resp = draft_lobby_req.json()

        _id = draft_lobby_resp["id"]
        _blue_auth, _red_auth = draft_lobby_resp["auth"]
        blue_url = f"http://prodraft.leagueoflegends.com?draft={_id}&auth={_blue_auth}&locale=en_US"
        red_url = f"http://prodraft.leagueoflegends.com?draft={_id}&auth={_red_auth}&locale=en_US"
        spec_url = f"http://prodraft.leagueoflegends.com?draft={_id}&locale=en_US"

        message = (
            f"BLUE TEAM:\n{blue_url}\n\nRED TEAM:\n{red_url}\n\nSPEC:\n{spec_url}\n"
        )

        self.broke = True

        await ctx.send(message)
