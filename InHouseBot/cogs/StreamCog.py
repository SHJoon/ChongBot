import discord
import os
from functools import wraps
from tempfile import NamedTemporaryFile

import gspread
from oauth2client.service_account import ServiceAccountCredentials

from discord.ext import commands

SHEET_NAME_IDX = 1
SHEET_ID_IDX = 2
SHEET_URL_IDX = 3

creds = None
gclient = None
google_oauth_json = None

if "GOOGLE_OAUTH_JSON" in os.environ:
    google_oauth_json = os.environ["GOOGLE_OAUTH_JSON"]
elif os.path.isfile("InHouseTest.json"):
    print("Grabbed local json file for test spreadsheet")
    with open("InHouseTest.json", "r") as f:
        google_oauth_json = f.read()

# Ugh, why can't open work on the StringIO class
f = NamedTemporaryFile(mode="w+", delete=False)
f.write(google_oauth_json)
f.flush()

scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/drive",
    ]
    
creds = ServiceAccountCredentials.from_json_keyfile_name(
        f.name, scope
    )

gclient = gspread.authorize(creds)


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
                    gclient.login()
                    print(msg)
                    mtries -= 1
            return await f(*args, **kwargs)

        return f_retry  # true decorator

    return deco_retry


class StreamCog(commands.Cog):
    def __init__(self, bot):

        self.creds = creds
        self.gclient = gclient
        self._init_sheet()
        self.sheet_name = None

    def _init_sheet(self):
        if "GOOGLE_OAUTH_JSON" in os.environ:
            self.sheet_name = "InHouseData"
        elif os.path.isfile("InHouseTest.json"):
            self.sheet_name = "InHouseDataTest"

        self.sheet = gclient.open(self.sheet_name).worksheet("Stream_URL")

        # Lets cache on init
        self.cache = self.sheet.get_all_values()

    @commands.command()
    @retry_authorize(gspread.exceptions.APIError)
    async def addstream(self, ctx, url=""):
        """ Configure your stream to our database! """
        user = ctx.message.author

        # If user exists, just update stream and exit
        # We can cache since if we add a new user, we update anyways
        for idx, row in enumerate(self.cache):
            if row[SHEET_ID_IDX - 1] == str(user.id):
                self.sheet.update_cell(idx + 1, SHEET_URL_IDX, url)
                # Update our cache
                row[SHEET_URL_IDX - 1] = url

                return

        # Otherwise add an entire new row for the user
        userlist = [user.name, str(user.id), url]
        self.sheet.append_row(userlist)

        # Update cache
        self.cache.append(userlist)

    @commands.command()
    @retry_authorize(gspread.exceptions.APIError)
    async def stream(self, ctx, member:discord.Member = None):
        """ Post your own stream. """
        user = ctx.message.author
        personid = None
        if member is not None:
            personid = member.id
        else:
            personid = user.id

        for row in self.cache:
            if row[SHEET_ID_IDX - 1] == str(personid):
                msg = row[SHEET_URL_IDX-1]
                return await ctx.send(msg)

        # User not found
        if member is not None:
            await ctx.send(
                f"{member.name} does not have any stream set up yet!"
                )
        else:
            await ctx.send(
            "You do not have any stream set up yet. Use !addstream to configure."
            )

    @commands.command()
    @retry_authorize(gspread.exceptions.APIError)
    async def streams(self, ctx):
        """ Show the list of streams. """
        max_name_len = max([len(x[1]) for x in self.cache[1:]])

        # We are not using SHEET_* constants becuase this is a python array
        # representation of the data, not indexing remotely
        msg = "".join(
            [
                "**{0: <{pad}}** :\t{1}\n".format(
                    row[SHEET_NAME_IDX-1], f"<{row[SHEET_URL_IDX-1]}>", pad=max_name_len
                )
                for row in self.cache[1:]
            ]
        )
        await ctx.send(msg)

    # WIP
    """
    async def get_stream_url(self, ctx, member:discord.Member):
        for row in self. cache:
            if row[SHEET_ID_IDX - 1] == str(member.id):
                return row[SHEET_URL_IDX - 1]
        return None
    
    @commands.command()
    async def test(self, ctx):
        print("----------------------")
        msg = "Currently Streaming:\n"
        for member in ctx.guild.members:
            print(member.activity)
            if member.activity == None:
                continue
            if any(str(member.id) in sublist for sublist in self.cache) == True:
                if member.activity.type == 3:
                    url = await self.get_stream_url(ctx, member)
                    msg += f"{member.name}: <{url}>\n"
        await ctx.send(msg)"""