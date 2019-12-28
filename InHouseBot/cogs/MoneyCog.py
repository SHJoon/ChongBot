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

        # Variables for !break command
        self.client = httpx.AsyncClient()
        self.broke = False
        self.blue_team_name = "Blue Side"
        self.red_team_name = "Red Side"

        self.blue_team_bet = {}
        self.red_team_bet = {}

    def _init_sheet(self):
        if "GOOGLE_OAUTH_JSON" in os.environ:
            self.sheet_name = "InHouseData"
        elif os.path.isfile("InHouseTest.json"):
            self.sheet_name = "InHouseDataTest"
            
        self.sheet = gclient.open(self.sheet_name).worksheet("Money_Database")
        self.sheet2 = gclient.open(self.sheet_name).worksheet("Player_Score")

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
            if row[SHEET_ID_IDX - 1] == str(author.id):
                await ctx.send(f"{author.name} has {row[SHEET_MONEY_IDX - 1]} NunuBucks.")
                return

        await ctx.send("You have not joined our currency database yet! Use `!join$` now!")
    
    async def is_positive_money(self, ctx, money):
        """ Lazy function to check if amount is Non-negative """
        if money < 0:
            await ctx.send("The amount of money has to be positive!")
            return False
        else:
            return True

    @is_approved()
    @commands.command(name="add$")
    @retry_authorize(gspread.exceptions.APIError)
    async def cmd_add(self, ctx, member:discord.Member, money:int):
        """ Add money to target member(ADMIN USE ONLY) """
        if await self.is_positive_money(ctx, money):
            for idx, row in enumerate(self.cache):
                if row[SHEET_ID_IDX - 1] == str(member.id):
                    current_money = int(row[SHEET_MONEY_IDX - 1])
                    new_money = current_money + money
                    self.sheet.update_cell(idx + 1, SHEET_MONEY_IDX, new_money)
                    row[SHEET_MONEY_IDX - 1] = new_money
    
    @is_approved()
    @commands.command(name="remove$")
    @retry_authorize(gspread.exceptions.APIError)
    async def cmd_remove(self, ctx, member:discord.Member, money:int):
        """ Remove money from target member(ADMIN USE ONLY) """
        money = -money
        await ctx.invoke(self.cmd_add(ctx, member, money))
    
    @commands.command()
    @retry_authorize(gspread.exceptions.APIError)
    async def give(self, ctx, member:discord.Member, money:int):
        """ Give some of your money to select person (!give @person amount)"""
        if await self.is_positive_money(ctx, money):
            author = ctx.message.author
            for idx, row in enumerate(self.cache):
                # Deduct amount from command invoker
                if row[SHEET_ID_IDX - 1] == str(author.id):
                    row[SHEET_MONEY_IDX - 1] = int(row[SHEET_MONEY_IDX - 1]) - money
                    self.sheet.update_cell(idx + 1, SHEET_MONEY_IDX, row[SHEET_MONEY_IDX - 1])
                # Give amount to target person
                if row[SHEET_ID_IDX - 1] == str(member.id):
                    row[SHEET_MONEY_IDX - 1] = int(row[SHEET_MONEY_IDX - 1]) + money
                    self.sheet.update_cell(idx + 1, SHEET_MONEY_IDX, row[SHEET_MONEY_IDX - 1])
    
    @commands.command()
    async def bet(self, ctx, team:str = "", money:int = 0):
        """ Bet on the team you think will win! Can only be used after !break is used. (!bet team amount) """
        # !break will collect name/id of the players from each team via voice channels
        if self.broke:
            # Betting amount has to be greater than 0.
            if await self.is_positive_money(ctx, money):
                author = ctx.message.author
                # Give error if betting amount is more than how much you own.
                for row in self.cache:
                    if row[SHEET_ID_IDX - 1] == str(author.id):
                        if int(row[SHEET_MONEY_IDX - 1]) < money:
                            await ctx.send("You don't have enough money to bet that amount!")
                            return

                if team.lower() == "blue":
                    # For replacing existing bet, return the money.
                    for member_id, bet in self.blue_team_bet.items():
                        if author.id == member_id:
                            for row in self.cache:
                                if row[SHEET_ID_IDX - 1] == str(author.id):
                                    row[SHEET_MONEY_IDX - 1] = int(row[SHEET_MONEY_IDX - 1]) + bet

                     # Add the author to a list/dict for blue team, with how much they bet.
                    self.blue_team_bet[author.id] = money
                    for row in self.cache:
                        if row[SHEET_ID_IDX - 1] == str(author.id):
                            row[SHEET_MONEY_IDX - 1] = int(row[SHEET_MONEY_IDX - 1]) - money

                elif team.lower() == "red":
                    # For replacing existing bet, return the money first, then put in the new bet.
                    for member_id, bet in self.red_team_bet.items():
                        if author.id == member_id:
                            for row in self.cache:
                                if row[SHEET_ID_IDX - 1] == str(author.id):
                                    row[SHEET_MONEY_IDX - 1] = int(row[SHEET_MONEY_IDX - 1]) + bet

                    # Add the author to a list/dict for red team, with how much they bet.
                    self.red_team_bet[author.id] = money
                    for row in self.cache:
                        if row[SHEET_ID_IDX - 1] == str(author.id):
                            row[SHEET_MONEY_IDX - 1] = int(row[SHEET_MONEY_IDX - 1]) - money
                elif team == "":
                    await ctx.send("You need to choose a team to bet on! For example, `!bet 500 Blue`")
                    return
                else:
                    await ctx.send("Team choices are either Blue or Red.")
        else:
            await ctx.send("You need to finalize the team with `!break` to start betting!")
    
    @commands.command()
    async def bets(self, ctx):
        """ Show the list of bets """
        server = ctx.guild
        message = f"**Blue Team multiplier:** {self.blue_multiplier}\
        \n**Red Team multiplier:** {self.red_multiplier}\
        \n**Blue Team Bets**"
        for member_id, bet_amt in self.blue_team_bet.items():
            member = discord.utils.get(server.members, id=member_id)
            name = member.nick if member.nick else member.name
            message += f"\n{name}: {bet_amt} NunuBucks"
        
        message += "\n**Red Team Bets**"
        for member_id, bet_amt in self.red_team_bet.items():
            member = discord.utils.get(server.members, id=member_id)
            name = member.nick if member.nick else member.name
            message += f"\n{name}: {bet_amt} NunuBucks"
        
        await ctx.send(message)
    
    async def update_whole_sheet(self):
        """ Update the whole spreadsheet. Used to minimize API calls """
        cache_len = len(self.cache)
        sheet_range_A1 = f'A1:C{cache_len}'
        cell_list = self.sheet.range(sheet_range_A1)
        index = 0
        for row in self.cache:
            for val in row:
                cell_list[index].value = val
                index += 1
        self.sheet.update_cells(cell_list)

    @is_approved()
    @commands.command(aliases=["payout"])
    @retry_authorize(gspread.exceptions.APIError)
    async def win(self, ctx, team = ""):
        """ Decide on who the winner is, and distribute the winnings accordingly! """
        if team.lower() == "blue":
            # Give the Blue team members their winnings.
            for row in self.cache:
                for member in self.blue_team:
                    if str(member.id) == row[SHEET_ID_IDX - 1]:
                        row[SHEET_MONEY_IDX - 1] = int(row[SHEET_MONEY_IDX - 1]) + 100
            # Grab the list/dict for blue team, calculate how much they won, and distribute accordingly.
            for member_id in self.blue_team_bet:
                self.blue_team_bet[member_id] *= self.blue_multiplier
                for row in self.cache:
                    if row[SHEET_ID_IDX - 1] == str(member_id):
                        row[SHEET_MONEY_IDX - 1] = int(row[SHEET_MONEY_IDX - 1]) + int(self.blue_team_bet[member_id])
        elif team.lower() == "red":
            # Give the Red team members their winnings.
            for row in self.cache:
                for member in self.red_team:
                    if str(member.id) == row[SHEET_ID_IDX - 1]:
                        row[SHEET_MONEY_IDX - 1] = int(row[SHEET_MONEY_IDX - 1]) + 100
            # Grab the list/dict for red team, calculate how much they won, and distribute accordingly.
            for member_id in self.red_team_bet:
                self.red_team_bet[member_id] *= self.red_multiplier
                for row in self.cache:
                    if row[SHEET_ID_IDX - 1] == str(member_id):
                        row[SHEET_MONEY_IDX - 1] = int(row[SHEET_MONEY_IDX - 1]) + int(self.red_team_bet[member_id])
        else:
            await ctx.send("The possible choices are either Blue or Red! For example: `!win Blue`")
            return

        self.broke = False
        self.blue_team_bet.clear()
        self.red_team_bet.clear()
        await self.update_whole_sheet()
    
    @commands.command()
    async def reset(self, ctx):
        """ Reset the bets and return all the money. """
        # Grab the list of both Blue/Red team bets, and return the money.
        if self.broke:
            # Return the money to participants
            for row in self.cache:
                for member in self.blue_team:
                    if str(member.id) == row[SHEET_ID_IDX - 1]:
                        row[SHEET_MONEY_IDX - 1] = int(row[SHEET_MONEY_IDX - 1]) + 50
                for member in self.red_team:
                    if str(member.id) == row[SHEET_ID_IDX - 1]:
                        row[SHEET_MONEY_IDX - 1] = int(row[SHEET_MONEY_IDX - 1]) + 50
            # Return the betting money for blue team
            for member_id, bet in self.blue_team_bet.items():
                for row in self.cache:
                    if row[SHEET_ID_IDX - 1] == str(member_id):
                        row[SHEET_MONEY_IDX - 1] = int(row[SHEET_MONEY_IDX - 1]) + bet
            # Return the betting money for red team
            for member_id, bet in self.red_team_bet.items():
                for row in self.cache:
                    if row[SHEET_ID_IDX - 1] == str(member_id):
                        row[SHEET_MONEY_IDX - 1] = int(row[SHEET_MONEY_IDX - 1]) + bet
        else:
            await ctx.send("Can only be used after !break is called!")
    
    @commands.command()
    async def steal(self, ctx, member:discord.Member):
        """ Steal money from target person (!steal @person) """
        # We can add as many funny URL's as we want
        image_URLs = ["https://i.redd.it/1wbz4b15vcd31.jpg"]
        image_URL = random.choice(image_URLs)
        embed = discord.Embed()
        embed.set_image(url=image_URL)
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

        # Deduct entry fee from every players
        for row in self.cache:
            for member in self.blue_team:
                if str(member.id) == row[SHEET_ID_IDX - 1]:
                    row[SHEET_MONEY_IDX - 1] = int(row[SHEET_MONEY_IDX - 1]) - 50
            for member in self.red_team:
                if str(member.id) == row[SHEET_ID_IDX - 1]:
                    row[SHEET_MONEY_IDX - 1] = int(row[SHEET_MONEY_IDX - 1]) - 50

        # Organize score of each teams
        blue_team_scores = []
        red_team_scores = []

        for row in self.cache2:
            for member in self.blue_team:
                if str(member.id) == row[SHEET_ID_IDX - 1]:
                    blue_team_scores.append(float(row[SHEET_SCORE_IDX - 1]))
            for member in self.red_team:
                if str(member.id) == row[SHEET_ID_IDX - 1]:
                    red_team_scores.append(float(row[SHEET_SCORE_IDX - 1]))
        
        blue_scores = 0
        red_scores = 0

        self.blue_multiplier = 0
        self.red_multiplier = 0

        for score in blue_team_scores:
            blue_scores += score
        for score in red_team_scores:
            red_scores += score
        
        self.blue_multiplier = blue_scores/(len(blue_team_scores))
        self.red_multiplier = red_scores/(len(red_team_scores))


    @commands.command(hidden=True)
    async def datatest(self, ctx):
        print(self.broke)
        await ctx.send(f"Blue team bets: {self.blue_team_bet}")
        await ctx.send(f"Red team bets: {self.red_team_bet}")
        print(self.blue_team)
        print(self.red_team)
        #print(self.blue_multiplier)
        await ctx.send(f"Blue team multiplier: {self.blue_multiplier}")
        #print(self.red_multiplier)
        await ctx.send(f"Red team multiplier: {self.red_multiplier}")