import asyncio
import discord
from discord.ext import commands

approved_roles = ["Admin", "Bot", "Mod"]

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
        self.queueid = None

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
            # Use queue to replace !leggo
            await self._ready(ctx)
        else:
            await ctx.send("The queue is closed.")
    
    @commands.command(aliases=["forceadd","fjoin", "fadd"])
    async def forcejoin(self, ctx, member: discord.Member):
        """ Force another user to join the queue with an @"""
        name = member.nick if member.nick else member.name
        if member.id not in self.queue:
            self.queue.append(member.id)
            await ctx.invoke(self._queue)
            await self._ready(ctx)
        else:
            await ctx.send(f"{name} is already in the queue!")
            await ctx.invoke(self._queue)
    
    async def _ready(self, ctx):
        if len(self.queue) == 10:
            server = ctx.guild
            for member_id in self.queue:
                member = discord.utils.get(server.members, id=member_id)
                await ctx.send(member.mention)
            await ctx.send("10 MEN TIME LESGOO")
            self.queue = []
        return
    
    @commands.command(aliases=["forcedrop","forceleave","fremove","fdrop","fleave"])
    async def forceremove(self, ctx, member: discord.Member):
        """ Force another user to drop from the queue with an @"""
        name = member.nick if member.nick else member.name
        if member.id in self.queue:
            self.queue.remove(member.id)
            await ctx.send(f"{name} has been removed from the queue.")
            await ctx.invoke(self._queue)
        else:
            await ctx.send(f"{name} was not in the queue!")
            await ctx.invoke(self._queue)
    
    @commands.command(aliases=["leave", "drop"])
    async def remove(self, ctx):
        """ Remove yourself from the queue """
        author = ctx.message.author
        message = ""
        if author.id in self.queue:
            self.queue.remove(author.id)
            await ctx.send("You have been removed from the queue.")
            await ctx.invoke(self._queue)
            if message != "":
                await ctx.send(message)
        else:
            await ctx.send("You were not in the queue.")
    
    @commands.command(name="queue", aliases=["lobby", "q"], pass_context=True)
    async def _queue(self, ctx):
        """ See who's up next! """
        server = ctx.guild
        if self.queueid is not None:
            await self.delete_prev_q(ctx)
        message = f"**Gaming time**: {self.qtime}\n"
        for place, member_id in enumerate(self.queue):
            member = discord.utils.get(server.members, id=member_id)
            message += f"**#{place+1}** : {member.name}\n"
        if len(self.queue) == 0:
            message += f"Queue is empty."
        embed = discord.Embed(title=message, colour=discord.Colour.green())
        messages = await ctx.send(embed=embed)
        self.queueid = messages.id
    
    async def delete_prev_q(self, ctx):
        queuemessage = await ctx.fetch_message(self.queueid)
        await queuemessage.delete()
    
    @commands.command(aliases=["qtime","settime","time"])
    async def queuetime(self, ctx, *, _time):
        """ Set gaming time """
        self.qtime = _time

    @commands.command(pass_context=True)
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
    @commands.command(pass_context=True)
    async def clear(self, ctx):
        """ Clears the queue (ADMIN ONLY) """
        self.queue = []
        self.qtime = "None set yet"
        await ctx.send("Queue has been cleared")
    
    @is_approved()
    @commands.command(pass_context=True)
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
        _message = await ctx.send("Time for some 10 mens! Join the lobby @here")
        # Since the queue is used as lobby now, commenting out the rest of code for now
        """
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
                #await ctx.send("Timing out our gaming call, try again later :(")
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
        """
