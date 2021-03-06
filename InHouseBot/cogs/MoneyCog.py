import discord
import httpx
import os
import random
import asyncio
import copy
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

        # For In-House spreadsheet
        self.baron_id = 663256952742084637
        self.peasant_id = 663605505809186847
        self.chief_id = 651544745868525597
        self.blue_team_id = 689334904822956050
        self.red_team_id = 689334969524551729
        # For Test spreadsheet
        self.rich_test_id = 665644125286039552
        self.poor_test_id = 665644198053150730
        self.chief_test_id = 677310051731636239
        self.blue_test_id = 689336261793808390
        self.red_test_id = 689336322875588712

        self._init_sheet()

        # Variables for !prodraft command
        self.client = httpx.AsyncClient()
        self.broke = False
        self.blue_team_name = "Blue Side"
        self.red_team_name = "Red Side"

        # Variables for !break command
        self.blue_team = []
        self.red_team = []
        self.blue_team_bet = {}
        self.red_team_bet = {}
        self.blue_winnings = 0
        self.red_winnings = 0
        self.bets_msg = None

        self.side_bets = {}
        self.side_bets_msg = None
        
        # Lock is implemented due to the structural design of the currency system
        # Due to the oauth reauthorization system, temporary cache is used for every command
        # that directly accesses google spreadsheet. Without the lock, using these commands
        # in sequence too quick can create many bugs
        self.lock = asyncio.Lock()

    def _init_sheet(self):
        if "GOOGLE_OAUTH_JSON" in os.environ:
            self.sheet_name = "InHouseData"
            self.rich_id = self.baron_id
            self.poor_id = self.peasant_id
            self.high_mmr_id = self.chief_id
            self.blue_role_id = self.blue_team_id
            self.red_role_id = self.red_team_id
        elif os.path.isfile("InHouseTest.json"):
            self.sheet_name = "InHouseDataTest"
            self.rich_id = self.rich_test_id
            self.poor_id = self.poor_test_id
            self.high_mmr_id = self.chief_test_id
            self.blue_role_id = self.blue_test_id
            self.red_role_id = self.red_test_id
            
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
    
    async def get_ranks(self, cached, userid:int):
        """ Returns current rank of given player """
        money_rank, mmr_rank = None, None
        for row in cached[1:]:
            if int(row[SHEET_ID_IDX - 1]) == userid:
                money_rank = row[SHEET_MONEY_RANK_IDX - 1]
                mmr_rank = row[SHEET_MMR_RANK_IDX - 1]
                break
        return money_rank, mmr_rank
    
    async def calculate_ranks(self, ctx, cached):
        """ Sort the cache by ranks and update them """
        self.money_ranking = sorted(cached[1:], key=lambda inner: int(inner[2]),reverse=True)
        self.mmr_ranking = sorted(cached[1:], key=lambda inner: float(inner[3]),reverse=True)

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
    
    async def assign_roles(self, ctx):
        """ Assign proper roles to each person based on money."""
        guild = ctx.guild
        # Remove existing baron roles, and assign new ones
        highest_money = int(self.money_ranking[0][2])
        rich_role = guild.get_role(self.rich_id)
        for member in rich_role.members:
            await member.remove_roles(rich_role)
        for name, id_, money, mmr, money_rank, mmr_rank, games, wins in self.money_ranking:
            member = discord.utils.get(guild.members, id=int(id_))
            if int(money) == highest_money:
                await member.add_roles(rich_role)
            else:
                break
        # Remove existing peasant roles, and assign new ones
        lowest_money = int(self.money_ranking[-1][2])
        poor_role = guild.get_role(self.poor_id)
        for person in poor_role.members:
            await person.remove_roles(poor_role)
        for name, id_, money, mmr, money_rank, mmr_rank, games, wins in reversed(self.money_ranking):
            member = discord.utils.get(guild.members, id=int(id_))
            if int(money) == lowest_money:
                await member.add_roles(poor_role)
            else:
                break
        # Remove existing chief roles, and assign new ones
        highest_mmr = str(self.mmr_ranking[0][3])
        chief_role = guild.get_role(self.high_mmr_id)
        for member in chief_role.members:
            await member.remove_roles(chief_role)
        for name, id_, money, mmr, money_rank, mmr_rank, games, wins in self.mmr_ranking:
            member = discord.utils.get(guild.members, id=int(id_))
            if str(mmr) == highest_mmr:
                await member.add_roles(chief_role)
            else:
                break
    
    async def update_whole_sheet(self, cached):
        """ Update the whole spreadsheet. """
        sheet_range_A2 = f'A2:H{len(cached)}'
        cell_list = self.sheet.range(sheet_range_A2)
        index = 0
        for row in self.mmr_ranking:
            for val in row:
                cell_list[index].value = val
                index += 1
        self.sheet.update_cells(cell_list)

    @is_approved()
    @commands.command(hidden=True)
    @retry_authorize(gspread.exceptions.APIError)
    async def update_the_sheet(self, ctx):
        """ (ADMIN) Force update the sheet manually """
        await self.calculate_ranks(ctx, self.cache)
        await self.update_whole_sheet(self.cache)

    @commands.command(name="join$")
    @retry_authorize(gspread.exceptions.APIError)
    async def cmd_join(self, ctx, member:discord.Member=None):
        """ Join our currency database! """
        user = userid = money_rank = mmr_rank = None
        async with self.lock:
            temp_cache = copy.deepcopy(self.cache)
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
            temp_cache.append(userlist)
            await self.calculate_ranks(ctx, temp_cache)
            money_rank, mmr_rank = await self.get_ranks(temp_cache, userid)
            userlist = [user, str(userid), "1000", "1400", money_rank, mmr_rank, 0, 0]
            temp_cache[-1] = userlist
            await self.update_whole_sheet(temp_cache)
            self.cache = temp_cache

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
                    money_rank, mmr_rank = await self.get_ranks(self.cache, person.id)
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
                    money_rank, mmr_rank = await self.get_ranks(self.cache, author.id)
            avatar = author.avatar_url
        msg = ""
        if mmr_rank in (0,"0"):
            msg = f"Money: {money} NunuBucks (#{money_rank})\nMMR: You need to play a game!"
        else:
            msg = f"Money: {money} NunuBucks (#{money_rank})\nMMR: {mmr} (#{mmr_rank})"
        embed = discord.Embed(title=f"{name}'s profile", description=msg)
        embed.set_thumbnail(url=avatar)
        await ctx.send(embed=embed)
    
    @commands.group(aliases=["ranks", "ranking", "rankings"])
    async def rank(self, ctx):
        """ Display ranks of our server! !rank (money/mmr) page# """
        if ctx.invoked_subcommand is None:
            cmd = ctx.message.content.split(" ", 1)
            key = cmd[1]
            message = ""
            title = f"{key} Rank"
            guild = ctx.guild
            userlist = []
            for row in self.cache[1:]:
                if int(row[SHEET_GAMES_IDX - 1]) < 5:
                    continue
                else:
                    user = discord.utils.get(guild.members, id=int(row[SHEET_ID_IDX - 1]))
                    userlist.append(user)
            random.shuffle(userlist)
            for idx, user in enumerate(userlist):
                message += f"**#{idx+1}**: {user.name}\n"
            embed = discord.Embed(title=title, description=message, colour = discord.Colour.dark_green())
            await ctx.send(embed=embed)

    @rank.command(aliases=["$", "rich"])
    async def money(self, ctx):
        message = ""
        title = "Money Rank"
        for idx, (name, id_, money, mmr, money_rank, mmr_rank, games, wins) in enumerate(self.money_ranking):
            if money_rank in  (1,"1"):
                message += f"\U0001F451: {name} - ${money}\n"
                continue
            message += f"**#{money_rank}**: {name} - ${money}\n"
        if message == "":
            message = "No one in this page!"
        embed = discord.Embed(title=title, description=message, colour = discord.Colour.gold())
        await ctx.send(embed=embed)
    
    @rank.command()
    async def mmr(self, ctx):
        message = ""
        title = "MMR Rank"
        for idx, (name, id_, money, mmr, money_rank, mmr_rank, games, wins) in enumerate(self.mmr_ranking):
            if mmr_rank in (0,"0"):
                continue
            mmr = float(mmr)
            if mmr_rank in  (1,"1"):
                message += f"\U0001F451: {name} - {int(mmr)}\n"
                continue
            message += f"**#{mmr_rank}**: {name} - {int(mmr)}\n"
        if message == "":
            message = "No one in this page!"
        embed = discord.Embed(title=title, description=message, colour = discord.Colour.orange())
        await ctx.send(embed=embed)
    
    @is_approved()
    @commands.command(name="add$")
    @retry_authorize(gspread.exceptions.APIError)
    async def cmd_add(self, ctx, member:discord.Member, money:int):
        """ (ADMIN) Add money to target member """
        async with self.lock:
            temp_cache = copy.deepcopy(self.cache)
            if await self.is_in_database(str(member.id)):
                if await self.is_positive_money(ctx, money):
                    for idx, row in enumerate(temp_cache):
                        if row[SHEET_ID_IDX - 1] == str(member.id):
                            current_money = int(row[SHEET_MONEY_IDX - 1])
                            new_money = current_money + money
                            row[SHEET_MONEY_IDX - 1] = new_money
                            break
            else:
                await ctx.send("The member is not part of the database yet!")
                return
            await self.calculate_ranks(ctx, temp_cache)
            await self.update_whole_sheet(temp_cache)
            await ctx.send(f"{member.name} has been given {money} NunuBucks.")
            self.cache = temp_cache
    
    @is_approved()
    @commands.command(name="remove$")
    @retry_authorize(gspread.exceptions.APIError)
    async def cmd_remove(self, ctx, member:discord.Member, money:int):
        """ (ADMIN) Remove money from target member """
        async with self.lock:
            temp_cache = copy.deepcopy(self.cache)

            if not await self.is_in_database(str(member.id)):
                await ctx.send("The member is not part of the database yet!")
                return

            if await self.is_positive_money(ctx, money):
                for idx, row in enumerate(temp_cache):
                    if row[SHEET_ID_IDX - 1] == str(member.id):
                        current_money = int(row[SHEET_MONEY_IDX - 1])
                        new_money = current_money - money
                        row[SHEET_MONEY_IDX - 1] = new_money
                        break
                    
            await self.calculate_ranks(ctx, temp_cache)
            await self.update_whole_sheet(temp_cache)
            await ctx.send(f"{member.name} has been deducted {money} NunuBucks.")
            self.cache = temp_cache
    
    @commands.command()
    @retry_authorize(gspread.exceptions.APIError)
    async def give(self, ctx, member:discord.Member, money:int):
        """ Give some of your money to select person (!give @person amount)"""
        async with self.lock:
            temp_cache = copy.deepcopy(self.cache)
            if not await self.is_positive_money(ctx, money):
                return

            current_money = await self.get_current_money(ctx)

            if not await self.has_enough_money(ctx, current_money, money):
                return
            elif not await self.is_in_database(str(ctx.message.author.id)):
                await ctx.send("You're not in the database yet! Use `!join$` now!")
                return
            elif not await self.is_in_database(str(member.id)):
                await ctx.send("The person is not in the database yet!")
                return

            author = ctx.message.author
            for idx, row in enumerate(temp_cache):
                # Deduct amount from command invoker
                if row[SHEET_ID_IDX - 1] == str(author.id):
                    row[SHEET_MONEY_IDX - 1] = int(row[SHEET_MONEY_IDX - 1]) - money
                # Give amount to target person
                if row[SHEET_ID_IDX - 1] == str(member.id):
                    row[SHEET_MONEY_IDX - 1] = int(row[SHEET_MONEY_IDX - 1]) + money

            await self.calculate_ranks(ctx, temp_cache)
            await self.update_whole_sheet(temp_cache)
            await ctx.send(f"{ctx.author.name} has given {member.name} {money} NunuBucks.")
            self.cache = temp_cache
    
    @commands.command()
    async def bet(self, ctx, team:str = "", money:int = 0):
        """ Bet on the team you think will win! (!bet team amount) """
        if not self.broke:
            await ctx.send("You need to finalize the team with `!break` to start betting!")
            return
        
        author = ctx.message.author
        if not await self.is_in_database(str(author.id)):
            await ctx.send("You're not in the database yet! Use `!join$` now!")
            return    
        elif not self.bet_toggle:
            await ctx.send("You need to bet within betting time to be able to bet!")
            return
        elif not await self.is_positive_money(ctx, money):
            return

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
                                break
                        break
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
                                break
                        break
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

    @is_approved()
    @commands.command(aliases=["payout"])
    @retry_authorize(gspread.exceptions.APIError)
    async def win(self, ctx, team = ""):
        """ (ADMIN) Decide on who the winner is, and payout accordingly! """
        if not self.broke:
            await ctx.send("You need to finalize the team with `!break` to start betting!")
            return
        async with self.lock:
            winning_team = None
            guild = ctx.guild
            msg = ""
            temp_cache = copy.deepcopy(self.cache)
            if team.lower() == "blue":
                temp_blue_bets = copy.deepcopy(self.blue_team_bet)
                # Give the Blue team members their winnings.
                # Additionally, calculate the new MMR of each players

                # Blue team when blue win
                for member in self.blue_team:
                    for row in temp_cache:
                        if str(member.id) == row[SHEET_ID_IDX - 1]:
                            row[SHEET_MONEY_IDX - 1] = int(row[SHEET_MONEY_IDX - 1]) + self.blue_winnings
                            old_mmr = float(row[SHEET_MMR_IDX - 1])
                            new_mmr = old_mmr + (32 * (1 - self.blue_team_win))
                            row[SHEET_MMR_IDX - 1] = new_mmr
                            row[SHEET_GAMES_IDX - 1] = int(row[SHEET_GAMES_IDX - 1]) + 1
                            row[SHEET_WINS_IDX - 1] = int(row[SHEET_WINS_IDX - 1]) + 1
                            break
                # Red team when blue win
                for member in self.red_team:
                    for row in temp_cache:
                        if str(member.id) == row[SHEET_ID_IDX - 1]:
                            old_mmr = float(row[SHEET_MMR_IDX - 1])
                            new_mmr = old_mmr + (32 * (0 - (1 - self.blue_team_win)))
                            row[SHEET_MMR_IDX - 1] = new_mmr
                            row[SHEET_GAMES_IDX - 1] = int(row[SHEET_GAMES_IDX - 1]) + 1
                            break
                # Grab the list/dict for blue team, calculate how much they won, and distribute accordingly.
                for member_id in temp_blue_bets:
                    temp_blue_bets[member_id] *= (1 + self.blue_multiplier)
                    member = discord.utils.get(guild.members, id=member_id)
                    msg += f"{member.name}: {int(temp_blue_bets[member_id])}\n"
                    for row in temp_cache:
                        if row[SHEET_ID_IDX - 1] == str(member_id):
                            row[SHEET_MONEY_IDX - 1] = int(row[SHEET_MONEY_IDX - 1]) + int(temp_blue_bets[member_id])
                            break
                winning_team = "Blue Team"
            elif team.lower() == "red":
                temp_red_bets = copy.deepcopy(self.red_team_bet)
                # Give the Red team members their winnings.
                # Red team when red win
                for member in self.red_team:
                    for row in temp_cache:
                        if str(member.id) == row[SHEET_ID_IDX - 1]:
                            row[SHEET_MONEY_IDX - 1] = int(row[SHEET_MONEY_IDX - 1]) + self.red_winnings
                            old_mmr = float(row[SHEET_MMR_IDX - 1])
                            new_mmr = old_mmr + (32 * (1 - (1 - self.blue_team_win)))
                            row[SHEET_MMR_IDX - 1] = new_mmr
                            row[SHEET_GAMES_IDX - 1] = int(row[SHEET_GAMES_IDX - 1]) + 1
                            row[SHEET_WINS_IDX - 1] = int(row[SHEET_WINS_IDX - 1]) + 1
                            break
                # Blue team when red win
                for member in self.blue_team:
                    for row in temp_cache:
                        if str(member.id) == row[SHEET_ID_IDX - 1]:
                            old_mmr = float(row[SHEET_MMR_IDX - 1])
                            new_mmr = old_mmr + (32 * (0 - self.blue_team_win))
                            row[SHEET_MMR_IDX - 1] = new_mmr
                            row[SHEET_GAMES_IDX - 1] = int(row[SHEET_GAMES_IDX - 1]) + 1
                            break
                # Grab the list/dict for red team, calculate how much they won, and distribute accordingly.
                for member_id in temp_red_bets:
                    temp_red_bets[member_id] *= (1 + self.red_multiplier)
                    member = discord.utils.get(guild.members, id=member_id)
                    msg += f"{member.name}: {int(temp_red_bets[member_id])}\n"
                    for row in temp_cache:
                        if row[SHEET_ID_IDX - 1] == str(member_id):
                            row[SHEET_MONEY_IDX - 1] = int(row[SHEET_MONEY_IDX - 1]) + int(temp_red_bets[member_id])
                            break
                winning_team = "Red Team"
            else:
                await ctx.send("The possible choices are either Blue or Red! For example: `!win Blue`")
                return
            if msg == "":
                msg = "No payout this time!"
            await self.calculate_ranks(ctx, temp_cache)
            await self.update_whole_sheet(temp_cache)
            message = await ctx.send(f"{winning_team} has won! Now distributing the payout...")
            avatar = message.author.avatar_url
            embed = discord.Embed(title="Bet Payouts",description=msg, colour = discord.Colour.gold())
            embed.set_thumbnail(url=avatar)
            await ctx.send(embed=embed)

            blue_team_role = guild.get_role(self.blue_role_id)
            for member in blue_team_role.members:
                await member.remove_roles(blue_team_role)
            red_team_role = guild.get_role(self.red_role_id)
            for member in red_team_role.members:
                await member.remove_roles(red_team_role)

            self.broke = False
            self.blue_multiplier = 0
            self.red_multiplier = 0
            self.blue_team_bet.clear()
            self.red_team_bet.clear()
            self.blue_team.clear()
            self.red_team.clear()
            self.cache = temp_cache
    
    @commands.command()
    async def sidebet(self, ctx, topic, money:int):
        """ Bet on which topic you think will win! (!bet topic amount) """
        topic = topic.upper()
        author = ctx.message.author

        if not await self.is_in_database(str(author.id)):
            await ctx.send("You're not in the database yet! Use `!join$` now!")
            return
        elif not await self.is_positive_money(ctx, money):
            return
        
        current_money = await self.get_current_money(ctx)
        # For replacing existing bet, return the money
        # Iterate through each topics
        for bets in self.side_bets:
            if (author.id in self.side_bets[bets]) and (topic == bets):
                for member_id, bet in self.side_bets[bets].items():
                    if author.id == member_id:
                        for row in self.cache:
                            if row[SHEET_ID_IDX - 1] == str(author.id):
                                if money > (current_money + bet):
                                    await ctx.send("You don't have enough money to bet that amount!")
                                    return
                                row[SHEET_MONEY_IDX - 1] = int(row[SHEET_MONEY_IDX - 1]) + bet
                                break
                        break
                break
            else:
                if money > current_money:
                    await ctx.send("You don't have enough money to bet that amount!")
                    return
        if topic in self.side_bets:
            self.side_bets[topic].update({author.id:money})
        else:
            self.side_bets[topic] = {author.id:money}
        for row in self.cache:
            if row[SHEET_ID_IDX - 1] == str(author.id):
                row[SHEET_MONEY_IDX - 1] = int(row[SHEET_MONEY_IDX - 1]) - money
                break
        await ctx.invoke(self.sidebets)
    
    @is_approved()
    @commands.command()
    @retry_authorize(gspread.exceptions.APIError)
    async def sidewin(self, ctx, topic):
        """ (ADMIN) Decide on who the winner is, and payout accordingly for side bets! """
        async with self.lock:
            topic = topic.upper()
            if topic not in self.side_bets:
                await ctx.send("That is not one of the choice for sidebets!")
                return

            temp_cache = copy.deepcopy(self.cache)
            guild = ctx.guild
            msg = ""
            for member_id, bet in self.side_bets[topic].items():
                for row in temp_cache:
                    if row[SHEET_ID_IDX - 1] == str(member_id):
                        payout = bet * 2
                        row[SHEET_MONEY_IDX - 1] = str(int(row[SHEET_MONEY_IDX - 1]) + (payout))
                        member = discord.utils.get(guild.members, id=member_id)
                        msg += f"{member.name}: {payout}\n"
                        break

            await self.calculate_ranks(ctx, temp_cache)
            await self.update_whole_sheet(temp_cache)
            message = await ctx.send(f"Winner: **{topic}**. Distributing payout(s)...")
            avatar = message.author.avatar_url
            embed = discord.Embed(title="Side Bet Payouts",description=msg, colour = discord.Colour.dark_gold())
            embed.set_thumbnail(url=avatar)
            await ctx.send(embed=embed)
            self.side_bets.clear()
            self.cache = temp_cache

    @is_approved()
    @commands.command(name="register")
    async def _register(self, ctx, team, *members:discord.Member):
        """ (ADMIN) Register players on the respective teams. """
        guild = ctx.guild
        embed = discord.Embed()
        message = ""
        if team == "blue":
            message += "**Blue Team members:**"
            blue_team_role = guild.get_role(self.blue_role_id)
            self.blue_team.clear()
            for member in blue_team_role.members:
                await member.remove_roles(blue_team_role)
            for member in members:
                self.blue_team.append(member)
                await member.add_roles(blue_team_role)
                message += f"\n{member.name}"
            embed.description = message
            embed.colour = discord.Colour.blue()
            await ctx.send(embed=embed)
        elif team == "red":
            message += "**Red Team members:**"
            red_team_role = guild.get_role(self.red_role_id)
            self.red_team.clear()
            for member in red_team_role.members:
                await member.remove_roles(red_team_role)
            for member in members:
                self.red_team.append(member)
                await member.add_roles(red_team_role)
                message += f"\n{member.name}"
            embed.description = message
            embed.colour = discord.Colour.red()
            await ctx.send(embed=embed)
        else:
            await ctx.send("The format is `!register team @person @person...`")
    
    @commands.command()
    async def prodraft(self, ctx):
        """ Generates a prodraft lobby """
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
        blue_url = f"<http://prodraft.leagueoflegends.com?draft={_id}&auth={_blue_auth}&locale=en_US>"
        red_url = f"<http://prodraft.leagueoflegends.com?draft={_id}&auth={_red_auth}&locale=en_US>"
        spec_url = f"<http://prodraft.leagueoflegends.com?draft={_id}&locale=en_US>"

        message = (
            f"BLUE TEAM:\n{blue_url}\n\nRED TEAM:\n{red_url}\n\nSPEC:\n{spec_url}\n"
        )

        await ctx.send(message)
    
    @commands.command(name="break")
    async def _break(self, ctx):
        """ Generates a prodraft lobby and records blue/red team members. """

        if not self.blue_team:
            await ctx.send("You must register **blue team** members using !register command.")
            return
        elif not self.red_team:
            await ctx.send("You must register **red team** members using !register command.")
            return

        await ctx.invoke(self.prodraft)

        self.broke = True

        blue_channel = red_channel = None
        if "GOOGLE_OAUTH_JSON" in os.environ:
            blue_channel = ctx.guild.get_channel(689335228933996568)
            red_channel = ctx.guild.get_channel(689335273502670911)
        else:
            blue_channel = ctx.guild.get_channel(689336015713992741)
            red_channel = ctx.guild.get_channel(689336062589665303)

        await blue_channel.send("This is start of a new session.")
        await red_channel.send("This is start of a new session.")

        # If the player is not in the database yet, add them to the database.
        for member in self.blue_team:
            if not await self.is_in_database(str(member.id)):
                await ctx.invoke(self.cmd_join, member)

        for member in self.red_team:
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

        self.blue_winnings = int(red_avg_MMR / len(red_team_MMRs))
        self.red_winnings = int(blue_avg_MMR / len(blue_team_MMRs))

        if self.blue_winnings < 200:
            self.blue_winnings = 200
        if self.red_winnings < 200:
            self.red_winnings < 200

        self.bet_toggle = True
        await ctx.send("**Betting starts now! You have 15 minutes until the bets close.**")
        await ctx.invoke(self.bets)
        await asyncio.sleep(480)
        await ctx.send("**The bet will close in 7 minutes!**")
        await asyncio.sleep(240)
        await ctx.send("<:Bonesaw:670046963735068694> I GOT YOU FOR 3 MINUTES, **3 MINUTES OF BET TIME LEFT** <:Bonesaw:670046963735068694>")
        await asyncio.sleep(180)
        self.bet_toggle = False
        await ctx.send("**The bets are now closed!**")
        await ctx.invoke(self.bets)
    
    @commands.command()
    async def bets(self, ctx):
        """ Show the list of bets """
        guild = ctx.guild
        embed = discord.Embed()
        if self.bets_msg is not None:
            await self.bets_msg.delete()
        
        message = f"**Blue Team winnings:** {self.blue_winnings}\n\
            **Red Team winnings:** {self.red_winnings}"
        embed.description = message

        message = "**Blue Team Multiplier:** {:.2f} \n \
            **Red Team Multiplier:** {:.2f}".format(1 + self.blue_multiplier, 1 + self.red_multiplier)
        embed.add_field(name = "\u200b", value = message, inline = False)

        message = "**Blue Team Bets**"
        for member_id, bet_amt in self.blue_team_bet.items():
            member = discord.utils.get(guild.members, id=member_id)
            name = member.nick if member.nick else member.name
            message += f"\n{name}: {bet_amt}"
        embed.add_field(name="\u200b",value = message,inline=True)
        
        message = "**Red Team Bets**"
        for member_id, bet_amt in self.red_team_bet.items():
            member = discord.utils.get(guild.members, id=member_id)
            name = member.nick if member.nick else member.name
            message += f"\n{name}: {bet_amt}"
        embed.add_field(name="\u200b",value = message,inline=True)
        embed.colour=discord.Colour.green()
        
        embed.set_footer(text="Use !bets to display this message.\n!bet blue/red amount")
        self.bets_msg = await ctx.send(embed=embed)
        await ctx.message.delete()
    
    @commands.command()
    async def sidebets(self, ctx):
        """ Show the list of side bets """
        guild = ctx.guild
        embed = discord.Embed ()
        if self.side_bets_msg is not None:
            await self.side_bets_msg.delete()

        for topic in self.side_bets:
            message = ""
            for member_id, bet_amt in self.side_bets[topic].items():
                member = discord.utils.get(guild.members, id=member_id)
                name = member.nick if member.nick else member.name
                message += f"\n{name}: {bet_amt}"
            embed.add_field(name=topic,value = message,inline=True)
        embed.colour=discord.Colour.dark_orange()
        
        embed.set_footer(text="Use !sidebets to display this message.\n!sidebet topic amount")
        self.side_bets_msg = await ctx.send(embed=embed)
        await ctx.message.delete()

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
        await ctx.send(f"Betting is open for {num} minute(s)")
        await asyncio.sleep(minute)
        await ctx.send("Betting is now closed.")
        self.bet_toggle = False
    
    @is_approved()
    @commands.command()
    async def reset(self, ctx):
        """ (ADMIN) Reset the bets and return all the money. """
        guild = ctx.guild
        # Return the betting money for blue team
        for member_id, bet in self.blue_team_bet.items():
            for row in self.cache:
                if row[SHEET_ID_IDX - 1] == str(member_id):
                    row[SHEET_MONEY_IDX - 1] = int(row[SHEET_MONEY_IDX - 1]) + bet
                    break
        # Return the betting money for red team
        for member_id, bet in self.red_team_bet.items():
            for row in self.cache:
                if row[SHEET_ID_IDX - 1] == str(member_id):
                    row[SHEET_MONEY_IDX - 1] = int(row[SHEET_MONEY_IDX - 1]) + bet
                    break
        # Remove "Blue Team" roles
        blue_team_role = guild.get_role(self.blue_team_id)
        for member in blue_team_role.members:
            await member.remove_roles(blue_team_role)
        # Remove "Red Team" roles
        red_team_role = guild.get_role(self.red_team_id)
        for member in red_team_role.members:
            await member.remove_roles(red_team_role)

        # Reset to all the default values
        self.broke = False
        self.blue_multiplier = 0
        self.red_multiplier = 0
        self.blue_team.clear()
        self.red_team.clear()
        self.blue_team_bet.clear()
        self.red_team_bet.clear()
        await ctx.send("All the bets have been reset.")
    
    @is_approved()
    @commands.command()
    async def sidereset(self, ctx):
        """ (ADMIN) Reset the side bets and return all the money. """
        for topic in self.side_bets:
            for member_id, bet in self.side_bets[topic].items():
                for row in self.cache:
                    if row[SHEET_ID_IDX - 1] == str(member_id):
                        row[SHEET_MONEY_IDX - 1] = int(row[SHEET_MONEY_IDX - 1]) + bet
                        break
        self.side_bets.clear()
        await ctx.send("All the sidebets have been reset.")

    @commands.command()
    async def steal(self, ctx, member:discord.Member):
        """ Steal money from target person (!steal @person) """
        # We can add as many funny URL's as we want
        image_URLs = [
            "https://i.redd.it/1wbz4b15vcd31.jpg", "https://cdn.discordapp.com/attachments/224084353779630080/670051783820705802/image0.jpg",
        ]
        image_URL = random.choice(image_URLs)
        embed = discord.Embed()
        embed.set_image(url=image_URL)
        await ctx.send(embed=embed)
