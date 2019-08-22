import discord
import httpx
from discord.ext import commands
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from gspread.utils import (
    rowcol_to_a1,
    fill_gaps,
)
class LeagueCog(commands.Cog):
    def __init__(self, bot, api_key=None):

        self.client = httpx.AsyncClient()

        # variables for gself.sheets
        self.numindex = 1
        self.nameindex = 2
        self.idindex = 3
        self.urlindex = 4

        # break is a keyword so we can't define it on class, interesting
        self.broke = False

    def _init_sheet(self):
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive.file",
            "https://www.googleapis.com/auth/drive",
        ]
        self.creds = ServiceAccountCredentials.from_json_keyfile_name(
            "InHouseData-43dcb8cebcde.json", scope
        )
        self.clients = gspread.authorize(self.creds)
        self.sheet = self.clients.open("InHouseData").sheet1
        data = self.sheet.get_all_records()


    @commands.command()
    async def addstream(self, ctx, url=""):
        """ Configure your stream to our database! """
        user = ctx.message.author
        # values_list = self.sheet.get_all_values()
        values_list = self.self.sheet.spreadself.sheet.values_get(self.self.sheet.title), {"key": self.api_key}

        try:
            # Error for fill_gaps; Not sure what the alternative for 'values' can be
            return fill_gaps(values_list["values"])
        except KeyError:
            return []

        for idx, element in enumerate(values_list):
            if element[2] == str(user.id):
                # self.sheet.update_cell(idx+1, self.urlindex, url)
                range_label = "%s!%s" % (
                    self.sheet.title,
                    rowcol_to_a1(idx + 1, self.urlindex),
                )
                data = self.sheet.spreadself.sheet.values_update(
                    range_label,
                    params={"valueInputOption": "USER_ENTERED", "key": self.api_key},
                    body={"values": [[url]]},
                )
                return data

        userlist = [len(values_list), user.name, str(user.id), url]
        # self.sheet.append_row(userlist)
        params = {"valueInputOption": "RAW", "key": self.api_key}

        body = {"values": [userlist]}
        self.sheet.spreadself.sheet.values_append(self.sheet.title, params, body)

    @commands.command()
    async def stream(self, ctx):
        """ Post your own stream """
        user = ctx.message.author
        # values_list = self.sheet.get_all_values()
        values_list = self.sheet.spreadself.sheet.values_get(self.sheet.title), {"key": self.api_key}

        try:
            return fill_gaps(values_list["values"])
        except KeyError:
            return []

        for _, element in enumerate(values_list):
            if element[2] == str(user.id):
                msg = element[3]
                await ctx.send(f"{msg}")
                return
        await ctx.send(
            "You do not have any stream set up yet. Use !addstream to configure."
        )

    @commands.command()
    async def streams(self, ctx):
        """ Show list of streams """
        # values_list = self.sheet.get_all_values()
        values_list = self.sheet.spreadself.sheet.values_get(self.sheet.title), {"key": self.api_key}

        try:
            return fill_gaps(values_list["values"])
        except KeyError:
            return []

        msg = ""
        for idx, element in enumerate(values_list):
            if idx == 0:
                continue
            else:
                msg += f"**{element[1]}**: {element[3]}\n"
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
