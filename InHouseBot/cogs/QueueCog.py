import asyncio
import discord
from discord.ext import commands

approved_roles = ["Admin"]

def is_approved():
    def predicate(ctx):
        author = ctx.message.author
        if any(role.name in approved_roles for role in author.roles):
            return True

    return commands.check(predicate)

class QueueCog(commands.Cog):
    def __init__(self, bot):
        self.queue = []
        self.qtoggle = True
        self.qtime = "None set yet"
        self.queuemsg = None
        self.readynum = 10

    @commands.command(aliases=["join"])
    async def add(self, ctx):
        """ Add yourself to the queue! """
        author = ctx.message.author
        if self.qtoggle:
            if author.id not in self.queue:
                self.queue.append(author.id)
            else:
                await ctx.send("You are already in the queue!")
            await ctx.invoke(self._queue)
        else:
            await ctx.send("The queue is closed.")
    
    @commands.command(aliases=["forcejoin","fjoin", "fadd"])
    async def forceadd(self, ctx, member: discord.Member):
        """ Force another user to join the queue with an @ """
        if self.qtoggle:
            name = member.nick if member.nick else member.name
            if member.id not in self.queue:
                self.queue.append(member.id)
                await ctx.invoke(self._queue)
            else:
                await ctx.send(f"{name} is already in the queue!")
                await ctx.invoke(self._queue)
        else:
            await ctx.send("The queue is closed.")
    
    @commands.command(name="ready", aliases=["go"])
    async def _ready(self, ctx):
        """ If everyone is ready to game, this command will ping them! """
        if len(self.queue) >= self.readynum:
            server = ctx.guild
            message = ""
            for member_id in self.queue[0:self.readynum]:
                member = discord.utils.get(server.members, id=member_id)
                message += member.mention
            await ctx.send(message)
            for _ in range(self.readynum):
                self.queue.pop(0)
            await ctx.send("10 MEN TIME LESGOO")
        else:
            await ctx.send("Not enough people in the lobby...")
        await ctx.invoke(self._queue)
    
    @commands.command(aliases=["leave", "drop"])
    async def remove(self, ctx):
        """ Remove yourself from the queue """
        author = ctx.message.author
        name = author.nick if author.nick else author.name
        if author.id in self.queue:
            self.queue.remove(author.id)
            await ctx.send(f"{name} has been removed from the queue.")
            await ctx.invoke(self._queue)
        else:
            await ctx.send("You were not in the queue.")
    
    @commands.command(aliases=["forcedrop","forceleave","fremove","fdrop","fleave"])
    async def forceremove(self, ctx, member: discord.Member):
        """ Force another user to drop from the queue with an @ """
        name = member.nick if member.nick else member.name
        if member.id in self.queue:
            self.queue.remove(member.id)
            await ctx.send(f"{name} has been removed from the queue.")
            await ctx.invoke(self._queue)
        else:
            await ctx.send(f"{name} was not in the queue!")
            await ctx.invoke(self._queue)
    
    @commands.command(name="queue", aliases=["lobby", "q"], pass_context=True)
    async def _queue(self, ctx):
        """ See who's up next! """
        server = ctx.guild
        if self.queuemsg is not None:
            try:
                await self.queuemsg.delete()
            except Exception:
                pass
        message = f"**Gaming time**: {self.qtime}\n"
        for place, member_id in enumerate(self.queue):
            member = discord.utils.get(server.members, id=member_id)
            name = member.nick if member.nick else member.name
            message += f"**#{place+1}** : {name}\n"
        if len(self.queue) == 0:
            message += f"Queue is empty."
        embed = discord.Embed(description=message, colour=discord.Colour.green())
        embed.set_footer(text="Join the queue with !add / Leave the queue with !leave")
        self.queuemsg = await ctx.send(embed=embed)
        await self.queuemsg.add_reaction("<:Join:668410201099206680>")
        await self.queuemsg.add_reaction("<:Drop:668410288667885568>")
        await self.queuemsg.add_reaction("<:RepostQueue:727428376331157585>")
        try:
            await ctx.message.delete()
        except Exception:
            pass
    
    @commands.command(aliases=["qtime","settime"])
    async def queuetime(self, ctx, *, _time):
        """ Set gaming time """
        self.qtime = _time
        await ctx.invoke(self._queue)

    @commands.command(hidden=True)
    async def position(self, ctx):
        """ Check your position in the queue """
        author = ctx.message.author
        if author.id in self.queue:
            _position = self.queue.index(author.id) + 1
            return ctx.send(f"You are **#{_position}** in the queue.")
        
        await ctx.send(
            f"You are not in the queue, please use {ctx.prefix}add to add yourself to the queue."
        )

    @commands.command(pass_context=True, name="next")
    async def _next(self, ctx, num=1):
        """ Call the next member in the queue """
        if len(self.queue) > 0:
            for _ in range(num):
                if len(self.queue) == 0:
                    await ctx.send("No one left in  the queue :(")
                    return
                member = discord.utils.get(ctx.guild.members, id=self.queue[0])
                await ctx.send(f"You are up **{member.mention}**! Have fun!")
                self.queue.remove(self.queue[0])
        else:
            await ctx.send("No one left in  the queue :(")

    @is_approved()
    @commands.command(hidden=True)
    async def clear(self, ctx):
        """ Clears the queue (ADMIN ONLY) """
        self.queue = []
        self.qtime = "None set yet"
        await ctx.send("Queue has been cleared")
    
    @is_approved()
    @commands.command(hidden=True)
    async def toggle(self, ctx):
        """ Toggles the queue (ADMIN ONLY) """
        self.qtoggle = not self.qtoggle
        if self.qtoggle:
            state = 'OPEN'
        else:
            state = 'CLOSED'
        await ctx.send(f'Queue is now {state}')

    @commands.command(pass_context=True)
    async def leggo(self, ctx, *, _time = "None set yet"):
        """ Tries to get a game ready """
        self.qtime = _time
        await ctx.send("Time for some 10 mens! Join the lobby @here")
        