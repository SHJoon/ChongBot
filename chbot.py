import discord
from discord.ext import commands

prefix = '!'  # change this to whatever prefix you'd like

bot = commands.Bot(command_prefix=prefix)

# add roles that can use some commands
approved_roles = ['Admin', 'Bot', 'Mod', 'Test role']


def is_approved():
    def predicate(ctx):
        author = ctx.message.author
        if any(role.name in approved_roles for role in author.roles):
            return True
    return commands.check(predicate)


@bot.event
async def on_ready():
    print(bot.user.name)
    print(bot.user.id)


class Queue(commands.Cog):

    def __init__(self, bot):
        ctx = bot
        self.queue = []
        self.qtoggle = False

    @commands.command(pass_context=True)
    async def add(self, ctx):
        ''': Add yourself to the queue!'''
        author = ctx.message.author
        if self.qtoggle:
            if author.id not in self.queue:
                self.queue.append(author.id)
                await ctx.send('you have been added to the queue.')
            else:
                await ctx.send('you are already in the queue!')
        else:
            await ctx.send('The queue is closed.')

    @commands.command(pass_context=True)
    async def remove(self, ctx):
        ''': Remove yourself from the queue'''
        author = ctx.message.author
        if author.id in self.queue:
            self.queue.remove(author.id)
            await ctx.send('you have been removed from the queue.')
        else:
            await ctx.send('you were not in the queue.')

    @commands.command(name='queue', pass_context=True)
    async def _queue(self, ctx):
        ''': See who's up next!'''
        server = ctx.guild
        message = ''
        for place, member_id in enumerate(self.queue):
            member = discord.utils.get(server.members, id=member_id)
            message += f'**#{place+1}** : {member.mention}\n'
        if message != '':
            await ctx.send(message)
        else:
            await ctx.send('Queue is empty')

    @commands.command(pass_context=True)
    async def position(self, ctx):
        ''': Check your position in the queue'''
        author = ctx.message.author
        if author.id in self.queue:
            _position = self.queue.index(author.id)+1
            await ctx.send(f'you are **#{_position}** in the queue.')
        else:
            await ctx.send(f'you are not in the queue, please use {prefix}add to add yourself to the queue.')

    @is_approved()
    @commands.command(pass_context=True, name='next')
    async def _next(self, ctx):
        ''': Call the next member in the queue'''
        if len(self.queue) > 0:
            member = discord.utils.get(
                ctx.guild.members, id=self.queue[0])
            await ctx.send(f'You are up **{member.mention}**! Have fun!')
            self.queue.remove(self.queue[0])

    @is_approved()
    @commands.command(pass_context=True)
    async def clear(self, ctx):
        ''': Clears the queue'''
        self.queue = []
        await ctx.send('Queue has been cleared')

    @is_approved()
    @commands.command(pass_context=True)
    async def toggle(self, ctx):
        ''': Toggles the queue'''
        self.qtoggle = not self.qtoggle
        if self.qtoggle:
            state = 'OPEN'
        else:
            state = 'CLOSED'
        await ctx.send(f'Queue is now {state}')


bot.add_cog(Queue(bot))

bot.run('NTk5MDMyNTg3ODI1OTcxMjEw.XnCW-Q.K_Nub6A4PfTPod-46_hsxtb_yKg')