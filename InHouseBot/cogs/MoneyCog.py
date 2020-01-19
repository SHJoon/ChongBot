import discord
import httpx
import os
import random
import asyncio
from functools import wraps
from tempfile import NamedTemporaryFile

import gspread
from oauth2client.service_account import ServiceAccountCredentials

from discord.ext import commands

SHEET_NAME_IDX = 1
SHEET_ID_IDX = 2
SHEET_MONEY_IDX = 3
SHEET_MMR_IDX = 4
SHEET_MONEY_RANK_IDX = 5
SHEET_MMR_RANK_IDX = 6
SHEET_GAMES_IDX = 7
SHEET_WINS_IDX = 8

creds = None
gclient = None
google_oauth_json = None

if "GOOGLE_OAUTH_JSON" in os.environ:
    google_oauth_json = os.environ["GOOGLE_OAUTH_JSON"]
elif os.path.isfile("InHouseTest.json"):
    print("Grabbed local json file for test spreadsheet.")
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
        self.rich_test_id = 665644125286039552
        self.poor_test_id = 665644198053150730
        self.baron_id = 663256952742084637
        self.peasant_id = 663605505809186847
        self.rich_id = None
        self.poor_id = None
        self._init_sheet()
        self.sheet_name = None

        # Variables for !break command
        self.client = httpx.AsyncClient()
        self.broke = False
        self.blue_team_name = "Blue Side"
        self.red_team_name = "Red Side"

        self.blue_team = []
        self.red_team = []
        self.blue_team_bet = {}
        self.red_team_bet = {}
        self.bets_msg = None

    def _init_sheet(self):
        if "GOOGLE_OAUTH_JSON" in os.environ:
            self.sheet_name = "InHouseData"
            self.rich_id = self.baron_id
            self.poor_id = self.peasant_id
        elif os.path.isfile("InHouseTest.json"):
            self.sheet_name = "InHouseDataTest"
            self.rich_id = self.rich_test_id
            self.poor_id = self.poor_test_id
            
        self.sheet = gclient.open(self.sheet_name).worksheet("Player_Profile")

        # Lets cache on init
        self.cache = self.sheet.get_all_values()
        # Ignoring column "I" of spreadsheet, as calculation is done on the spreadsheet
        self.cache = [x[:-1] for x in self.cache]
        self.money_ranking = sorted(self.cache[1:], key=lambda inner: int(inner[2]), reverse=True)
        self.mmr_ranking = sorted(self.cache[1:], key=lambda inner: float(inner[3]),reverse=True)

    async def is_positive_money(self, ctx, money):
        """ Lazy function to check if amount is Non-negative """
        if money < 0:
            await ctx.send("The amount of money has to be positive!")
            return False
        else:
            return True
    
    async def has_enough_money(self, ctx, current_money, arg_money):
        """ Check if invoker has enough money for the argument """
        if current_money >= arg_money:
            return True
        else:
            await ctx.send("You don't have enough money to do that.")
            return False

    async def is_in_database(self, element):
        """ Check if the element is in the cache """
        return any(element in sublist for sublist in self.cache)
    
    async def get_current_money(self,ctx):
        """ Retrieve how much the person has """
        author = ctx.message.author
        for row in self.cache:
            if row[SHEET_ID_IDX - 1] == str(author.id):
                return int(row[SHEET_MONEY_IDX - 1])
    
    async def update_whole_sheet(self):
        """ Update the whole spreadsheet. """
        sheet_range_A1 = f'A2:H{len(self.cache)}'
        cell_list = self.sheet.range(sheet_range_A1)
        index = 0
        for row in self.money_ranking:
            for val in row:
                cell_list[index].value = val
                index += 1
        self.sheet.update_cells(cell_list)
    
    async def calculate_ranks(self, ctx):
        """ Sort the cache by ranks and update them """
        self.money_ranking = sorted(self.cache[1:], key=lambda inner: int(inner[2]),reverse=True)
        self.mmr_ranking = sorted(self.cache[1:], key=lambda inner: float(inner[3]),reverse=True)

        prev_money = 0
        rank = 0
        for idx, (name, id_, money, mmr, money_rank, mmr_rank, games, wins) in enumerate(self.money_ranking):
            if money != prev_money:
                rank = idx + 1
            self.money_ranking[idx][4] = str(rank)
            prev_money = money

        prev_mmr = 0
        rank = 1
        index = 0
        for idx, (name, id_, money, mmr, money_rank, mmr_rank, games, wins) in enumerate(self.mmr_ranking):
            if games in (0,"0"):
                self.mmr_ranking[idx][5] = 0
            else: 
                if mmr != prev_mmr:
                    rank = index + 1
                self.mmr_ranking[idx][5] = str(rank)
                index += 1
            prev_mmr = mmr

        await self.assign_roles(ctx)
    
    async def get_ranks(self, userid:int):
        """ Returns current rank of given player """
        money_rank, mmr_rank = None, None
        for row in self.cache:
            if row[SHEET_ID_IDX - 1] == str(userid):
                money_rank = row[SHEET_MONEY_RANK_IDX - 1]
                mmr_rank = row[SHEET_MMR_RANK_IDX - 1]
                break
        return money_rank, mmr_rank
    
    async def assign_roles(self, ctx):
        """ Assign proper roles to each person based on money."""
        guild = ctx.guild
        # Remove existing baron roles, and assign new ones
        highest_money = self.money_ranking[0][2]
        rich_role = guild.get_role(self.rich_id)
        for member in rich_role.members:
            await member.remove_roles(rich_role)
        for name, id_, money, mmr, money_rank, mmr_rank, games, wins in self.money_ranking:
            member = discord.utils.get(guild.members, id=int(id_))
            if money == highest_money:
                await member.add_roles(guild.get_role(self.rich_id))
            else:
                break
        # Remove existing peasant roles, and assign new ones
        lowest_money = self.money_ranking[-1][2]
        poor_role = guild.get_role(self.poor_id)
        for person in poor_role.members:
            await person.remove_roles(poor_role)
        for name, id_, money, mmr, money_rank, mmr_rank, games, wins in reversed(self.money_ranking):
            member = discord.utils.get(guild.members, id=int(id_))
            if money == lowest_money:
                await member.add_roles(guild.get_role(self.poor_id))
            else:
                break

    @is_approved()
    @commands.command(hidden=True)
    @retry_authorize(gspread.exceptions.APIError)
    async def update_the_sheet(self, ctx):
        """ (ADMIN) Force update the sheet manually """
        await self.calculate_ranks(ctx)
        await self.update_whole_sheet()

    @commands.command(name="join$")
    @retry_authorize(gspread.exceptions.APIError)
    async def cmd_join(self, ctx, member:discord.Member=None):
        """ Join our currency database! """
        user = userid = money_rank = mmr_rank = None
        if member is not None:
            if await self.is_in_database(str(member.id)):
                await ctx.send(f"{member.name} is already part of our database!")
                return
            user = member.name
            userid = member.id
        else:
            author = ctx.message.author
            if await self.is_in_database(str(author.id)):
                await ctx.send("You have already joined our currency database!")
                return
            user = author.name
            userid = author.id
        
        userlist = [user, str(userid), "1000", "1400", 0, 0, 0, 0]
        self.cache.append(userlist)
        await self.calculate_ranks(ctx)
        money_rank, mmr_rank = await self.get_ranks(userid)
        userlist = [user, str(userid), "1000", "1400", money_rank, mmr_rank, 0, 0]
        self.cache[-1] = userlist
        await self.update_whole_sheet()

    @commands.command(aliases = ["$", "money", "fund", "funds", "cash", "mmr"])
    async def profile(self, ctx, person:discord.Member=None):
        """ View your bank/MMR! """
        name = money = money_rank = mmr = mmr_rank = avatar = None
        author = ctx.message.author
        if person is not None:
            if not await self.is_in_database(str(person.id)):
                await ctx.send("The person is not part of our currency database yet!")
                return

            name = person.name
            avatar = person.avatar_url
            for row in self.cache:
                if str(person.id) == row[SHEET_ID_IDX - 1]:
                    money = row[SHEET_MONEY_IDX - 1]
                    mmr = float(row[SHEET_MMR_IDX - 1])
                    mmr = int(mmr)
                    money_rank, mmr_rank = await self.get_ranks(person.id)
        else:
            if not await self.is_in_database(str(author.id)):
                await ctx.send("You have not joined our currency database yet! Use `!join$` now!")
                return

            name = author.name
            for row in self.cache:
                if str(author.id) == row[SHEET_ID_IDX - 1]:
                    money = row[SHEET_MONEY_IDX - 1]
                    mmr = float(row[SHEET_MMR_IDX - 1])
                    mmr = int(mmr)
                    money_rank, mmr_rank = await self.get_ranks(author.id)
            avatar = author.avatar_url
        msg = ""
        if mmr_rank in (0,"0"):
            msg = f"Money: {money} NunuBucks (#{money_rank})\nMMR: You need to play a game!"
        else:
            msg = f"Money: {money} NunuBucks (#{money_rank})\nMMR: {mmr} (#{mmr_rank})"
        embed = discord.Embed(title=f"{name}'s profile", description=msg)
        embed.set_thumbnail(url=avatar)
        await ctx.send(embed=embed)
    
    @commands.command(aliases=["ranks", "ranking", "rankings"])
    async def rank(self, ctx, key:str="", page:int=1):
        """ Display ranks of our server! !rank (money/mmr) page# """
        end_element = (page*15) - 1
        start_element = end_element - 14
        title = None
        message = ""
        if key.lower() == "money":
            title = "Money Rank"
            if page == 0:
                for idx, (name, id_, money, mmr, money_rank, mmr_rank, games, wins) in enumerate(self.money_ranking):
                    message += f"**#{money_rank}**: {name} - ${money}\n"
            else:
                for idx, (name, id_, money, mmr, money_rank, mmr_rank, games, wins) in enumerate(self.money_ranking):
                    if start_element <= idx <= end_element:
                        message += f"**#{money_rank}**: {name} - ${money}\n"
        elif key.lower() == "mmr":
            title = "MMR Rank"
            if page == 0:
                for idx, (name, id_, money, mmr, money_rank, mmr_rank, games, wins) in enumerate(self.mmr_ranking):
                    if mmr_rank in (0,"0"):
                        continue
                    mmr = float(mmr)
                    message += f"**#{mmr_rank}**: {name} - {int(mmr)}\n"
            else:
                for idx, (name, id_, money, mmr, money_rank, mmr_rank, games, wins) in enumerate(self.mmr_ranking):
                    if start_element <= idx <= end_element:
                        if mmr_rank in (0,"0"):
                            continue
                        mmr = float(mmr)
                        message += f"**#{mmr_rank}**: {name} - {int(mmr)}\n"
        else:
            await ctx.send("We have rankings based on either money or mmr! (`!rank money`) or (`!rank mmr`)")
            return
        if message == "":
            message = "No one in this page!"
        embed = discord.Embed(title=title, description=message)
        if key.lower() == "money":
            embed.colour = discord.Colour.gold()
        else:
            embed.colour = discord.Colour.greyple()
        embed.set_footer(text="To access different pages, !rank (money/mmr) (page#)")
        await ctx.send(embed=embed)
    
    @is_approved()
    @commands.command(name="add$")
    @retry_authorize(gspread.exceptions.APIError)
    async def cmd_add(self, ctx, member:discord.Member, money:int):
        """ (ADMIN) Add money to target member """
        if await self.is_in_database(str(member.id)):
            if await self.is_positive_money(ctx, money):
                for idx, row in enumerate(self.cache):
                    if row[SHEET_ID_IDX - 1] == str(member.id):
                        current_money = int(row[SHEET_MONEY_IDX - 1])
                        new_money = current_money + money
                        # self.sheet.update_cell(idx + 1, SHEET_MONEY_IDX, new_money)
                        row[SHEET_MONEY_IDX - 1] = new_money
                        break
        else:
            await ctx.send("The member is not part of the database yet!")
            return
        await self.calculate_ranks(ctx)
        await self.update_whole_sheet()
    
    @is_approved()
    @commands.command(name="remove$")
    @retry_authorize(gspread.exceptions.APIError)
    async def cmd_remove(self, ctx, member:discord.Member, money:int):
        """ (ADMIN) Remove money from target member """
        if await self.is_in_database(str(member.id)):
            if await self.is_positive_money(ctx, money):
                for idx, row in enumerate(self.cache):
                    if row[SHEET_ID_IDX - 1] == str(member.id):
                        current_money = int(row[SHEET_MONEY_IDX - 1])
                        new_money = current_money - money
                        # self.sheet.update_cell(idx + 1, SHEET_MONEY_IDX, new_money)
                        row[SHEET_MONEY_IDX - 1] = new_money
                        break
        else:
            await ctx.send("The member is not part of the database yet!")
            return
        await self.calculate_ranks(ctx)
        await self.update_whole_sheet()
    
    @commands.command()
    @retry_authorize(gspread.exceptions.APIError)
    async def give(self, ctx, member:discord.Member, money:int):
        """ Give some of your money to select person (!give @person amount)"""
        if await self.is_positive_money(ctx, money):
            current_money = await self.get_current_money(ctx)
            if await self.has_enough_money(ctx, current_money, money):
                if await self.is_in_database(str(ctx.message.author.id)):
                    if await self.is_in_database(str(member.id)):
                        author = ctx.message.author
                        for idx, row in enumerate(self.cache):
                            # Deduct amount from command invoker
                            if row[SHEET_ID_IDX - 1] == str(author.id):
                                row[SHEET_MONEY_IDX - 1] = int(row[SHEET_MONEY_IDX - 1]) - money
                                # self.sheet.update_cell(idx + 1, SHEET_MONEY_IDX, row[SHEET_MONEY_IDX - 1])
                            # Give amount to target person
                            if row[SHEET_ID_IDX - 1] == str(member.id):
                                row[SHEET_MONEY_IDX - 1] = int(row[SHEET_MONEY_IDX - 1]) + money
                                # self.sheet.update_cell(idx + 1, SHEET_MONEY_IDX, row[SHEET_MONEY_IDX - 1])
                    else:
                        await ctx.send("The person is not in the database yet!")
                        return
                else:
                    await ctx.send("You're not in the database yet! Use `!join$` now!")
                    return
            else:
                return
        await self.calculate_ranks(ctx)
        await self.update_whole_sheet()
    
    @commands.command()
    async def bet(self, ctx, team:str = "", money:int = 0):
        """ Bet on the team you think will win! (!bet team amount) """
        # !break will collect name/id of the players from each team via voice channels
        if self.broke:
            author = ctx.message.author
            if await self.is_in_database(str(author.id)):
                if self.bet_toggle:
                    # Betting amount has to be greater than 0.
                    if await self.is_positive_money(ctx, money):
                        # Give error if betting amount is more than how much you own.
                        current_money = await self.get_current_money(ctx)
                        if team.lower() == "blue":
                            # If you're in Red Team, you cannot bet for Blue Team.
                            for member in self.red_team:
                                if author.id == member.id:
                                    await ctx.send("You cannot bet on the opposing team!")
                                    return
                            # For replacing existing bet, return the money.
                            if author.id in self.blue_team_bet:
                                for member_id, bet in self.blue_team_bet.items():
                                    if author.id == member_id:
                                        for row in self.cache:
                                            if row[SHEET_ID_IDX - 1] == str(author.id):
                                                if money > (current_money + bet):
                                                    await ctx.send("You don't have enough money to bet that amount!")
                                                    return
                                                row[SHEET_MONEY_IDX - 1] = int(row[SHEET_MONEY_IDX - 1]) + bet
                            else:
                                if money > current_money:
                                    await ctx.send("You don't have enough money to bet that amount!")
                                    return

                            # Add the author to a list/dict for blue team, with how much they bet.
                            self.blue_team_bet[author.id] = money
                            for row in self.cache:
                                if row[SHEET_ID_IDX - 1] == str(author.id):
                                    row[SHEET_MONEY_IDX - 1] = int(row[SHEET_MONEY_IDX - 1]) - money

                        elif team.lower() == "red":
                            # If you're in Blue Team, you cannot bet for Red Team.
                            for member in self.blue_team:
                                if author.id == member.id:
                                    await ctx.send("You cannot bet on the opposing team!")
                                    return
                            # For replacing existing bet, return the money first, then put in the new bet.
                            if author.id in self.red_team_bet:
                                for member_id, bet in self.red_team_bet.items():
                                    if author.id == member_id:
                                        for row in self.cache:
                                            if row[SHEET_ID_IDX - 1] == str(author.id):
                                                if money > (current_money + bet):
                                                    await ctx.send("You don't have enough money to bet that amount!")
                                                    return
                                                row[SHEET_MONEY_IDX - 1] = int(row[SHEET_MONEY_IDX - 1]) + bet
                            else:
                                if current_money < money:
                                    await ctx.send("You don't have enough money to bet that amount!")
                                    return

                            # Add the author to a list/dict for red team, with how much they bet.
                            self.red_team_bet[author.id] = money
                            for row in self.cache:
                                if row[SHEET_ID_IDX - 1] == str(author.id):
                                    row[SHEET_MONEY_IDX - 1] = int(row[SHEET_MONEY_IDX - 1]) - money
                        elif team == "":
                            await ctx.send("You need to choose a team to bet on! For example, `!bet 500 Blue`")
                        else:
                            await ctx.send("Team choices are either Blue or Red.")
                        await ctx.invoke(self.bets)
                else:
                    await ctx.send("You need to bet within betting time to be able to bet!")
            else:
                await ctx.send("You're not in the database yet! Use `!join$` now!")
        else:
            await ctx.send("You need to finalize the team with `!break` to start betting!")
    
    @commands.command()
    async def bets(self, ctx):
        """ Show the list of bets """
        server = ctx.guild
        embed = discord.Embed()
        if self.bets_msg is not None:
            await self.bets_msg.delete()
        message = "**Blue Team Multiplier:** {:.2f} \n \
            **Red Team Multiplier:** {:.2f}".format(1 + self.blue_multiplier, 1 + self.red_multiplier)
        embed.description = message

        message = "**Blue Team Bets**"
        for member_id, bet_amt in self.blue_team_bet.items():
            member = discord.utils.get(server.members, id=member_id)
            name = member.nick if member.nick else member.name
            message += f"\n{name}: {bet_amt} NunuBucks"
        embed.add_field(name="\u200b",value = message,inline=True)
        
        message = "**Red Team Bets**"
        for member_id, bet_amt in self.red_team_bet.items():
            member = discord.utils.get(server.members, id=member_id)
            name = member.nick if member.nick else member.name
            message += f"\n{name}: {bet_amt} NunuBucks"
        embed.add_field(name="\u200b",value = message,inline=True)
        embed.colour=discord.Colour.green()
        
        # embed = discord.Embed(description=message, colour = discord.Colour.green())
        embed.set_footer(text="Use !bets to display this message.\n!bet blue/red amount")
        self.bets_msg = await ctx.send(embed=embed)
        await ctx.message.delete()

    @is_approved()
    @commands.command(aliases=["payout"])
    @retry_authorize(gspread.exceptions.APIError)
    async def win(self, ctx, team = ""):
        """ (ADMIN) Decide on who the winner is, and payout accordingly! """
        winning_team = None
        server = ctx.guild
        msg = ""
        if team.lower() == "blue":
            # Give the Blue team members their winnings.
            # Additionally, calculate the new MMR of each players
            for row in self.cache:
                # Blue team when blue win
                for member in self.blue_team:
                    if str(member.id) == row[SHEET_ID_IDX - 1]:
                        row[SHEET_MONEY_IDX - 1] = int(row[SHEET_MONEY_IDX - 1]) + 200
                        old_mmr = float(row[SHEET_MMR_IDX - 1])
                        new_mmr = old_mmr + (32 * (1 - self.blue_team_win))
                        row[SHEET_MMR_IDX - 1] = new_mmr
                        row[SHEET_GAMES_IDX - 1] = int(row[SHEET_GAMES_IDX - 1]) + 1
                        row[SHEET_WINS_IDX - 1] = int(row[SHEET_WINS_IDX - 1]) + 1
                # Red team when blue win
                for member in self.red_team:
                    if str(member.id) == row[SHEET_ID_IDX - 1]:
                        old_mmr = float(row[SHEET_MMR_IDX - 1])
                        new_mmr = old_mmr + (32 * (0 - (1 - self.blue_team_win)))
                        row[SHEET_MMR_IDX - 1] = new_mmr
                        row[SHEET_GAMES_IDX - 1] = int(row[SHEET_GAMES_IDX - 1]) + 1
            # Grab the list/dict for blue team, calculate how much they won, and distribute accordingly.
            for member_id in self.blue_team_bet:
                temp = self.blue_team_bet[member_id]
                self.blue_team_bet[member_id] *= (1 + self.blue_multiplier)
                member = discord.utils.get(server.members, id=member_id)
                msg += f"{member.name}: {int(self.blue_team_bet[member_id])}\n"
                for row in self.cache:
                    if row[SHEET_ID_IDX - 1] == str(member_id):
                        row[SHEET_MONEY_IDX - 1] = int(row[SHEET_MONEY_IDX - 1]) + int(self.blue_team_bet[member_id])
            winning_team = "Blue Team"
        elif team.lower() == "red":
            # Give the Red team members their winnings.
            for row in self.cache:
                # Red team when red win
                for member in self.red_team:
                    if str(member.id) == row[SHEET_ID_IDX - 1]:
                        row[SHEET_MONEY_IDX - 1] = int(row[SHEET_MONEY_IDX - 1]) + 200
                        old_mmr = float(row[SHEET_MMR_IDX - 1])
                        new_mmr = old_mmr + (32 * (1 - (1 - self.blue_team_win)))
                        row[SHEET_MMR_IDX - 1] = new_mmr
                        row[SHEET_GAMES_IDX - 1] = int(row[SHEET_GAMES_IDX - 1]) + 1
                        row[SHEET_WINS_IDX - 1] = int(row[SHEET_WINS_IDX - 1]) + 1
                # Blue team when red win
                for member in self.blue_team:
                    if str(member.id) == row[SHEET_ID_IDX - 1]:
                        old_mmr = float(row[SHEET_MMR_IDX - 1])
                        new_mmr = old_mmr + (32 * (0 - self.blue_team_win))
                        row[SHEET_MMR_IDX - 1] = new_mmr
                        row[SHEET_GAMES_IDX - 1] = int(row[SHEET_GAMES_IDX - 1]) + 1
            # Grab the list/dict for red team, calculate how much they won, and distribute accordingly.
            for member_id in self.red_team_bet:
                temp = self.red_team_bet[member_id]
                self.red_team_bet[member_id] *= (1 + self.red_multiplier)
                member = discord.utils.get(server.members, id=member_id)
                msg += f"{member.name}: {int(self.red_team_bet[member_id])}\n"
                for row in self.cache:
                    if row[SHEET_ID_IDX - 1] == str(member_id):
                        row[SHEET_MONEY_IDX - 1] = int(row[SHEET_MONEY_IDX - 1]) + int(self.red_team_bet[member_id])
            winning_team = "Red Team"
        else:
            await ctx.send("The possible choices are either Blue or Red! For example: `!win Blue`")
            return
        message = await ctx.send(f"{winning_team} has won! Now distributing the payout...")
        avatar = message.author.avatar_url
        embed = discord.Embed(title="Bet Payouts",description=msg, colour = discord.Colour.gold())
        embed.set_thumbnail(url=avatar)
        await ctx.send(embed=embed)
        self.broke = False
        self.blue_multiplier = 0
        self.red_multiplier = 0
        self.blue_team_bet.clear()
        self.red_team_bet.clear()
        await self.calculate_ranks(ctx)
        await self.update_whole_sheet()
    
    @is_approved()
    @commands.command(name="register")
    async def _register(self, ctx, team, *members:discord.Member):
        """ (ADMIN) Register players on the respective teams. """
        embed = discord.Embed()
        message = ""
        if team == "blue":
            message += "**Blue Team members:**"
            self.blue_team.clear()
            for member in members:
                self.blue_team.append(member)
                message += f"\n{member.name}"
            embed.description = message
            embed.colour = discord.Colour.blue()
            await ctx.send(embed=embed)
        elif team == "red":
            message += "**RED Team members:**"
            self.red_team.clear()
            for member in members:
                self.red_team.append(member)
                message += f"\n{member.name}"
            embed.description = message
            embed.colour = discord.Colour.red()
            await ctx.send(embed=embed)
        else:
            await ctx.send("The format is `!register team @person @person...`")
    
    @commands.command(name="break")
    async def _break(self, ctx):
        """ Generates a prodraft lobby and records blue/red team memebers. """

        if not self.blue_team:
            await ctx.send("You must register **blue team** members using !register command.")
            return
        elif not self.red_team:
            await ctx.send("You must register **red team** members using !register command.")
            return

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

        # If the player is not in the database yet, add them to the database.
        for member in self.blue_team:
            # is_in_database = any(str(member.id) in sublist for sublist in self.cache)
            if not await self.is_in_database(str(member.id)):
                await ctx.invoke(self.cmd_join, member)

        for member in self.red_team:
            # is_in_database = any(str(member.id) in sublist for sublist in self.cache)
            if not await self.is_in_database(str(member.id)):
                await ctx.invoke(self.cmd_join, member)

        # Organize score of each teams
        blue_team_MMRs = []
        red_team_MMRs = []

        for row in self.cache:
            for member in self.blue_team:
                if str(member.id) == row[SHEET_ID_IDX - 1]:
                    blue_team_MMRs.append(float(row[SHEET_MMR_IDX - 1]))
            for member in self.red_team:
                if str(member.id) == row[SHEET_ID_IDX - 1]:
                    red_team_MMRs.append(float(row[SHEET_MMR_IDX - 1]))
        
        blue_MMRs = 0
        red_MMRs = 0

        self.blue_multiplier = 0
        self.red_multiplier = 0

        for MMR in blue_team_MMRs:
            blue_MMRs += MMR
        for MMR in red_team_MMRs:
            red_MMRs += MMR
        
        blue_avg_MMR = blue_MMRs/(len(blue_team_MMRs))
        red_avg_MMR = red_MMRs/(len(red_team_MMRs))

        self.blue_team_win = blue_avg_MMR / (blue_avg_MMR + red_avg_MMR)

        self.blue_multiplier = (1 - self.blue_team_win) / self.blue_team_win
        self.red_multiplier = 1 / self.blue_multiplier

        self.bet_toggle = True
        await ctx.send("**Betting starts now! You have 15 minutes until the bets close.**")
        await ctx.invoke(self.bets)
        await asyncio.sleep(480)
        await ctx.send("**The bet will close in 7 minutes!**")
        await asyncio.sleep(420)
        self.bet_toggle = False
        await ctx.send("**The bets are now closed!**")
        await ctx.invoke(self.bets)
    
    @is_approved()
    @commands.command()
    async def bettoggle(self, ctx):
        """ (ADMIN) Toggle bets on/off """
        self.bet_toggle = not self.bet_toggle
        if self.bet_toggle:
            await ctx.send("Betting is now open.")
        else:
            await ctx.send("Betting is now closed.")
    
    @is_approved()
    @commands.command()
    async def extend(self, ctx, num:int):
        """ (ADMIN) Extend the betting time (!extend minutes)"""
        minute = num * 60
        self.bet_toggle = True
        await asyncio.sleep(minute)
        await ctx.send("Betting is now closed.")
        self.bet_toggle = False
    
    @is_approved()
    @commands.command()
    async def reset(self, ctx):
        """ (ADMIN) Reset the bets and return all the money. """
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
        # Reset to all the default values
        self.broke = False
        self.blue_multiplier = 0
        self.red_multiplier = 0
        self.blue_team_bet.clear()
        self.red_team_bet.clear()
        await ctx.send("All the bets have been reset.")

    @commands.command()
    async def steal(self, ctx, member:discord.Member):
        """ Steal money from target person (!steal @person) """
        # We can add as many funny URL's as we want
        image_URLs = ["https://i.redd.it/1wbz4b15vcd31.jpg"]
        image_URL = random.choice(image_URLs)
        embed = discord.Embed()
        embed.set_image(url=image_URL)
        await ctx.send(embed=embed)
