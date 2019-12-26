import discord
import httpx
import os
import random
from functools import wraps
from tempfile import NamedTemporaryFile

import gspread
from oauth2client.service_account import ServiceAccountCredentials

from discord.ext import commands

SHEET_NAME_IDX = 1
SHEET_ID_IDX = 2
SHEET_MONEY_IDX = 3
SHEET_SCORE_IDX = 3

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

approved_roles = ["Admin"]

def is_approved():
    def predicate(ctx):
        author = ctx.message.author
        if any(role.name in approved_roles for role in author.roles):
            return True

    return commands.check(predicate)

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


class MoneyCog(commands.Cog):
    def __init__(self, bot):

        self.creds = creds
        self.gclient = gclient
        self._init_sheet()
        self.sheet_name = None

        self.blue_team_bet = {}
        self.red_team_bet = {}
        self.blue_team_scores = []
        self.red_team_scores = []
        self.blue_multiplier = 0
        self.red_multiplier = 0

        # Variables for !break command
        self.client = httpx.AsyncClient()
        self.broke = False
        self.blue_team_name = "Blue Side"
        self.red_team_name = "Red Side"

    def _init_sheet(self):
        if "GOOGLE_OAUTH_JSON" in os.environ:
            self.sheet_name = "InHouseData"
        elif os.path.isfile("InHouseTest.json"):
            self.sheet_name = "InHouseDataTest"
            
        self.sheet = gclient.open(self.sheet_name).worksheet("Money")
        self.sheet2 = gclient.open(self.sheet_name).worksheet("PlayerScore")

        # Lets cache on init
        self.cache = self.sheet.get_all_values()
        self.cache2 = self.sheet2.get_all_values()
    
    @commands.command(name="join$")
    @retry_authorize(gspread.exceptions.APIError)
    async def cmd_join(self, ctx):
        """ Join our currency database! """
        user = ctx.message.author
        for row in self.cache:
            if row[SHEET_ID_IDX - 1] == str(user.id):
                await ctx.send("You have already joined our currency database!")
                return
        
        userlist = [user.name, str(user.id), "500"]
        self.sheet.append_row(userlist)

        self.cache.append(userlist)
    
    @commands.command(name = "$", aliases = ["money", "fund"])
    async def cmd_money(self, ctx):
        """ Check how much money you have! """
        author = ctx.message.author
        for row in self.cache:
            if row[SHEET_ID_IDX - 1] == author.id:
                await ctx.send(f"{author.name} has {row[SHEET_MONEY_IDX - 1]} WillumpBucks.")
                return

        await ctx.send("You have not joined our currency database yet! Use `!join$` now!")
    
    @is_approved()
    @commands.command(name="add$")
    @retry_authorize(gspread.exceptions.APIError)
    async def cmd_add(self, ctx, money:int, user:discord.Member):
        """ Add money to target member(ADMIN USE ONLY) """
        for idx, row in enumerate(self.cache):
            if row[SHEET_ID_IDX - 1] == str(user.id):
                current_money = int(row[SHEET_MONEY_IDX - 1])
                new_money = current_money + money
                self.sheet.update_cell(idx + 1, SHEET_MONEY_IDX, new_money)
                row[SHEET_MONEY_IDX - 1] = new_money
                return
        
        await ctx.send(f"{user.name} is not part of our currency database yet!")
    
    @is_approved()
    @commands.command(name="remove$")
    @retry_authorize(gspread.exceptions.APIError)
    async def cmd_remove(self, ctx, money:int, user:discord.Member):
        """ Remove money from target member(ADMIN USE ONLY) """
        for idx, row in enumerate(self.cache):
            if row[SHEET_ID_IDX - 1] == str(user.id):
                current_money = int(row[SHEET_MONEY_IDX - 1])
                new_money = current_money - money
                self.sheet.update_cell(idx + 1, SHEET_MONEY_IDX, new_money)
                row[SHEET_MONEY_IDX - 1] = new_money
                return
        
        await ctx.send(f"{user.name} is not part of our currency database yet!")
    
    @commands.command()
    @retry_authorize(gspread.exceptions.APIError)
    async def give(self, ctx, money:int, member:discord.Member):
        """ Give some of your money to select person (!give amount person)"""
        author = ctx.message.author
        for idx, row in enumerate(self.cache):
            # Deduct amount from command invoker
            if row[SHEET_ID_IDX - 1] == str(author.id):
                row[SHEET_MONEY_IDX - 1] -= money
                self.sheet.update_cell(idx + 1, SHEET_MONEY_IDX, row[SHEET_MONEY_IDX - 1])
            # Give amount to target person
            if row[SHEET_ID_IDX - 1] == str(member.id):
                row[SHEET_MONEY_IDX - 1] += money
                self.sheet.update_cell(idx + 1, SHEET_MONEY_IDX, row[SHEET_MONEY_IDX - 1])
    
    @commands.command()
    @retry_authorize(gspread.exceptions.APIError)
    async def bet(self, ctx, money:int, team:str = ""):
        """ Bet on the team you think will win! Can only be used after !break is used. (!bet amount team) """
        # !break will collect name/id of the players from each team via voice channels
        if self.broke:
            if money < 0:
                await ctx.send("The betting amount has to be positive integer!")
                return

            author = ctx.message.author
            if team.lower() == "blue":
                 # Add the author to a list/dict for blue team, with how much they bet.
                self.blue_team_bet[author.id] = money
            elif team.lower() == "red":
                # Add the author to a list/dict for red team, with how much they bet.
                self.red_team_bet[author.id] = money
            elif team == "":
                await ctx.send("You need to choose a team to bet on! For example, `!bet 500 Blue`")
                return
            else:
                await ctx.send("Team choices are either Blue or Red.")
                return

            # Deduct the bet amount
            for idx, row in enumerate(self.cache):
                    if row[SHEET_ID_IDX - 1] == str(author.id):
                        row[SHEET_MONEY_IDX - 1] -= money
                        self.sheet.update_cell(idx + 1, SHEET_MONEY_IDX, row[SHEET_MONEY_IDX - 1])
        else:
            await ctx.send("You need to finalize the team with `!break` to start betting!")
    
    @is_approved()
    @commands.command(aliases=["payout"])
    @retry_authorize(gspread.exceptions.APIError)
    async def win(self, ctx, team:str):
        """ Decide on who the winner is, and distribute the winnings accordingly! """
        if team.lower() == "blue":
            
            # Give the Blue team members their winnings.
            # Grab the list/dict for blue team, calculate how much they won, and distribute accordingly.
            self.broke = False
            pass
        elif team.lower() == "red":
            # Give the Red team members their winnings.
            # Grab the list/dict for red team, calculate how much they won, and distribute accordingly.
            self.broke = False
            pass
        else:
            await ctx.send("The possible choices are either Blue or Red!")
    
    @commands.command()
    @retry_authorize(gspread.exceptions.APIError)
    async def reset(self, ctx):
        """ Reset the bets and return all the money. """
        # Grab the list of both Blue/Red team bets, and return the money.
        pass
    
    @commands.command()
    async def steal(self, ctx, member:discord.Member):
        """ Steal money from target person (!steal @person) """
        embed = discord.Embed()
        embed.set_image(url="https://i.redd.it/1wbz4b15vcd31.jpg")
        await ctx.send(embed=embed)
    
    @commands.command(name="breaking")
    async def temp_break(self, ctx):
        """ Generates a prodraft lobby and records blue/red team memebers. """

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
                "team1Name": f"{self.blue_team_name}",
                "team2Name": f"{self.red_team_name}",
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

        await ctx.send(message)
        self.broke = True

        for person in self.cache2:
            for member in self.blue_team:
                if str(member.id) == person[SHEET_ID_IDX - 1]:
                    self.blue_team_scores.append(int(person[SHEET_SCORE_IDX - 1]))
        
        for person in self.cache2:
            for member in self.red_team:
                if str(member.id) == person[SHEET_ID_IDX - 1]:
                    self.blue_team_scores.append(int(person[SHEET_SCORE_IDX - 1]))
        
        blue_scores = 0
        red_scores = 0

        for score in self.blue_team_scores:
            blue_scores += score
        for score in self.red_team_scores:
            red_scores += score
        
        self.blue_multiplier = blue_scores/(len(self.blue_team_scores))
        self.red_multiplier = red_scores/(len(self.red_multiplier))


    @commands.command()
    async def test(self, ctx):
        print(self.broke)
        print(self.blue_team_bet)
        print(self.red_team_bet)