import discord
from discord.ext import commands
import random
import asyncio

prefix = "!"  # change this to whatever prefix you'd like
bot = commands.Bot(command_prefix=prefix)
# add roles that can use some commands
approved_roles = ["Admin", "Bot", "Mod"]


def is_approved():
    def predicate(ctx):
        author = ctx.message.author
        if any(role.name in approved_roles for role in author.roles):
            return True

    return commands.check(predicate)


@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(name="with Chong's feelings",))
    print(bot.user.name)
    print(bot.user.id)


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    if message.content == "W":
        await message.add_reaction("\U0001F1FC")
    elif message.content == "smH":
        await message.add_reaction("\U0001F1F8")
        await message.add_reaction("\U0001F1F2")
        await message.add_reaction("\U0001F1ED")
    elif message.content == "H town let's get it!":
        await message.add_reaction("\U0001F680")
        await message.add_reaction("\U0001F1FC")
    else:
        await bot.process_commands(message)


class Queue(commands.Cog):
    def __init__(self, bot):
        self.queue = []
        self.qtoggle = True
        #await bot.change_presence(game=discord.Game(name="with Chong's feelings", type=0))

    @commands.command(pass_context=True, name="commands")
    async def _commands(self, ctx):
        await ctx.send(
            "**!add** = Add yourself to the queue. \
                        \n**!remove** = Remove yourself from the queue.\
                        \n**!queue** = See the current queue.\
                        \n**!position** = See your current position in the queue.\
                        \n**!next** = Call the next person in the queue.\
                        \n**!next #** = Call the next # of people in the queue.\
                        \n**!clear** = Clear the queue. **(Admin use only)**\
                        \n**!toggle** = Toggle the queue On/Off. **(Admin use only)**\
                        \n**!stream** = Usually danny streams the game he's in.\
                        \n**!flip** = Heads or Tails.\
                        \n**!choose choice1,choice2,...** = Choose randomly from your own list of choices.\
                        \n**!roll AdX** = Roll X-sided die, A times. (Ex. 1d6 = roll 6-sided die 1 time.)\
                        \n**!captains** = Randomly choose captain from people that are currently in the voice chat.\
                        \n**!lulcaptains** = Same as !captains, but Danny style...\
                        \n**!leggo** = Drop an {at}here for 10-men. Will automatically choose captain after 10 people react.\
                        \n**!fuckchong** = Honestly, fuck him.\
                        \n**!grime** = Important slice of in-house history...\
                        \n**!ass** = It is the truth.\
                        \n**!morg** = Will always be funny.\
                        \n**!boys** = The boys are back in town. \
                        \n**!cool** = See if you're cool or not!"
        )

    @commands.command(pass_context=True)
    async def add(self, ctx):
        """: Add yourself to the queue!"""
        author = ctx.message.author
        if self.qtoggle:
            if author.id not in self.queue:
                self.queue.append(author.id)
                await ctx.send("you have been added to the queue.")
            else:
                await ctx.send("you are already in the queue!")
        else:
            await ctx.send("The queue is closed.")

    @commands.command(pass_context=True)
    async def remove(self, ctx):
        """: Remove yourself from the queue"""
        author = ctx.message.author
        if author.id in self.queue:
            self.queue.remove(author.id)
            await ctx.send("you have been removed from the queue.")
        else:
            await ctx.send("you were not in the queue.")

    @commands.command(name="queue", pass_context=True)
    async def _queue(self, ctx):
        """: See who's up next!"""
        server = ctx.guild
        message = ""
        for place, member_id in enumerate(self.queue):
            member = discord.utils.get(server.members, id=member_id)
            message += f"**#{place+1}** : {member.name}\n"
        if message != "":
            await ctx.send(message)
        else:
            await ctx.send("Queue is empty")

    @commands.command(pass_context=True)
    async def position(self, ctx):
        """: Check your position in the queue"""
        author = ctx.message.author
        if author.id in self.queue:
            _position = self.queue.index(author.id) + 1
            await ctx.send(f"you are **#{_position}** in the queue.")
        else:
            await ctx.send(
                f"you are not in the queue, please use {prefix}add to add yourself to the queue."
            )

    @commands.command(pass_context=True, name="next")
    async def _next(self, ctx, num=1):
        """: Call the next member in the queue"""
        if len(self.queue) > 0:
            for x in range(num):
                member = discord.utils.get(ctx.guild.members, id=self.queue[0])
                await ctx.send(f"You are up **{member.mention}**! Have fun!")
                self.queue.remove(self.queue[0])

    @is_approved()
    @commands.command(pass_context=True)
    async def clear(self, ctx):
        """: Clears the queue"""
        self.queue = []
        await ctx.send("Queue has been cleared")

    @is_approved()
    @commands.command(pass_context=True)
    async def toggle(self, ctx):
        """: Toggles the queue"""
        self.qtoggle = not self.qtoggle
        if self.qtoggle:
            state = "OPEN"
        else:
            state = "CLOSED"
        await ctx.send(f"Queue is now {state}")

    @commands.command(pass_context=True)
    async def stream(self, ctx):
        await ctx.send(f"https://www.twitch.tv/turbolobster")

    @commands.command(pass_context=True)
    async def fuckchong(self, ctx):
        msg = await ctx.send(f"FUCK CHONG")
        await msg.add_reaction("\U0001F1EB")
        await msg.add_reaction("\U0001F1FA")
        await msg.add_reaction("\U0001F1E8")
        await msg.add_reaction("\U0001F1F0")
        await msg.add_reaction("\U000021AA")
        await msg.add_reaction("\U0001F1ED")
        await msg.add_reaction("\U0001F1F4")
        await msg.add_reaction("\U0001F1F3")
        await msg.add_reaction("\U0001F1EC")
        emoji = (
            ":FuckChong:"
        )  # You need to use discord.utils.get to fetch the ID I think
        await msg.add_reaction(emoji)

    @commands.command(pass_context=True)
    async def ass(self, ctx):
        await ctx.send(f"CHONG IS AN ASS EATER")

    @commands.command(pass_context=True)
    async def grime(self, ctx):
        await ctx.send(
            f"On May 6th, 2019, Chong invited an ex-LCS player to the server..."
        )

    @commands.command(pass_context=True)
    async def morg(self, ctx):
        await ctx.send(
            f"https://media.discordapp.net/attachments/569646728224178184/598615204288397501/unknown.png?width=1250&height=676"
        )

    @commands.command(pass_context=True)
    async def boys(self, ctx):
        await ctx.send(
            f"https://i.imgflip.com/360ktl.jpg"
        )

    @commands.command(pass_context=True)
    async def cool(self, ctx):
        author = ctx.message.author
        #Chong's server ID
        if author.id == 172899191998251009:
            await ctx.send(
                f"You're grimey"
                )
        else:
            await ctx.send(
                f"You're cool! {author.mention}"
            )
    

    @commands.command(pass_context=True)
    async def flip(self, ctx):
        flip = ["Heads", "Tails"]
        ranflip = random.choice(flip)

        embed = discord.Embed(
            title = ranflip
        )

        if ranflip == "Heads":
            embed.set_image(
                url='https://lolskinshop.com/wp-content/uploads/2015/04/Poppy_2.jpg'
                )
            embed.colour = discord.Colour.orange()
        else:
            embed.set_image(
                url='https://2.bp.blogspot.com/-_1l8obImQmA/V3F9Z8MV3_I/AAAAAAAA8FI/Kcj-ALPCPoY5cTeaAgFtgYIg6qihz4XBgCLcB/s1600/Taric_Splash_4.jpg'
                )
            embed.colour = discord.Colour.blue()
        
        #https://nexus.leagueoflegends.com/wp-content/uploads/2018/08/Nunu_Bot_fqvx53j9ion1fxkr34ag.gif
        #https://media0.giphy.com/media/3oz8xCXbQDReF34WWs/giphy-downsized.gif
        #https://www.ssbwiki.com/images/b/bf/Fox_SSBM.jpg
        #https://www.ssbwiki.com/images/1/17/Falco_SSBM.jpg
        #https://lolskinshop.com/wp-content/uploads/2015/04/Poppy_2.jpg
        #https://2.bp.blogspot.com/-_1l8obImQmA/V3F9Z8MV3_I/AAAAAAAA8FI/Kcj-ALPCPoY5cTeaAgFtgYIg6qihz4XBgCLcB/s1600/Taric_Splash_4.jpg

        await ctx.send(embed=embed)


    @commands.command(pass_context=True)
    async def choose(self, ctx, *choices: str):
        await ctx.send(random.choice(choices))

    @commands.command()
    async def roll(self, ctx, dice: str):
        try:
            rolls, limit = map(int, dice.split("d"))
        except Exception:
            await ctx.send("AdX format only(A=number of die, X=number of faces)")
            return

        result = ", ".join(str(random.randint(1, limit)) for r in range(rolls))
        await ctx.send(result)

    @commands.command(pass_context=True)
    async def captains(self, ctx):
        """: Randomizes captains list from General Voice channel"""
        members = discord.utils.get(
            ctx.guild.channels, name="General", type=discord.ChannelType.voice
        ).members
        random.shuffle(members)
        message = ""
        for place, member in enumerate(members):
            name = member.nick if member.nick else member.name
            message += f"**#{place+1}** : {name}\n"
        if not message:
            message = "No voice lobby for captains draft"
        await ctx.send(message)

    @commands.command(pass_context=True)
    async def lulcaptains(self, ctx):
        """: Randomizes captains list from General Voice channel"""
        members = discord.utils.get(
            ctx.guild.channels, name="General", type=discord.ChannelType.voice
        ).members
        random.shuffle(members)
        message = ""
        alphabet = "abcdefghijklmnopqrstuvwxyz"
        for place, member in enumerate(members):
            name = member.nick if member.nick else member.name
            danny_name = ""
            for c in name:
                if (
                    random.randrange(100) <= 17
                ):  # Danny turing test is complete @ ~ 17% of mistype
                    danny_name += c + alphabet[random.randrange(len(alphabet))]
                else:
                    danny_name += c
            message += f"**#{place+1}** : {danny_name}\n"
        if not message:
            message = "No voice lobby for captains draft"
        await ctx.send(message)

    @commands.command(pass_context=True)
    async def leggo(self, ctx):
        """Tries to get a game ready"""

        _message = await ctx.send("Who gaming, react @here")
        react_count = 0
        reactions = []
        # open our queue for spill
        self.qtoggle = True
        self.queue = []
        # Let us timeout after 1:30 hour so we don't leak
        seconds_elapsed = 0
        while react_count < 10:
            # Let's not hog bot thread
            await asyncio.sleep(3)
            seconds_elapsed += 3
            if seconds_elapsed > 5400:
                await ctx.send("Timing out our gaming call, try again later :(")
                return
            # Must refetch message otherwise coroutine never revaluates msg cache
            message = await ctx.fetch_message(_message.id)
            reactions = message.reactions
            react_count = sum(
                map(lambda x: x.count, reactions)
            )  # Can't do length of list since a reaction can have multiple reacts

        message = "Game ready, let's fuckin goooooo: \n\n"
        users = []
        for reaction in reactions:
            _users = await reaction.users().flatten()
            users.extend(_users)

        for place, user in enumerate(users):
            name = user.nick if user.nick else user.name
            if place + 1 > 10:
                if user.id not in self.queue:
                    self.queue.append(user.id)
                    message += f"**#{place+1}**: {name} - added to queue"
            else:
                message += f"**#{place+1}** : {name}\n"

        await ctx.send(message)


bot.add_cog(Queue(bot))

# Place your token in a file called 'key' next to the script
with open("key", "r") as f:
    token = f.read().strip().strip("\n")

bot.run(token)
