from config import *
from log import *

import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
from typing import *
import api
import time

import utils

# loading token
load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')

bot = commands.Bot(command_prefix=PREFIXES, intents=discord.Intents.all(), help_command=None)
mg = api.Manager()


# errors

@bot.event
async def on_command_error(ctx: commands.Context, error):
    # not enough args
    if isinstance(error, commands.MissingRequiredArgument):
        log(f'{ctx.author} {ctx.author.id} missing required argument(s): {ctx.message.content}', level=ERROR)
        await ctx.reply(embed=ARGS_REQUIRED_EMBED, ephemeral=True)

    # missing required permissions
    elif isinstance(error, commands.MissingPermissions):
        log(f'{ctx.author} {ctx.author.id} missing permissions: {ctx.message.content}', level=ERROR)
        await ctx.reply(embed=MISSING_PERMS_EMBED, ephemeral=True)

    # unknown channel
    elif isinstance(error, commands.ChannelNotFound):
        log(f'{ctx.author} {ctx.author.id}\'s channel not found: {ctx.message.content}', level=ERROR)
        await ctx.reply(embed=UNKNOWN_CHANNEL_EMBED, ephemeral=True)

    # unknown user
    elif isinstance(error, commands.UserNotFound) or isinstance(error, commands.MemberNotFound):
        log(f'{ctx.author} {ctx.author.id}\'s user not found: {ctx.message.content}', level=ERROR)
        await ctx.reply(embed=UNKNOWN_USER_EMBED, ephemeral=True)

    # BOT missing required permissions
    elif isinstance(error, commands.BotMissingPermissions):
        log(f'{ctx.author} {ctx.author.id} did smth but bot can\'t: {ctx.message.content}', level=ERROR)
        await ctx.reply(embed=BOT_MISSING_PERMS_EMBED, ephemeral=True)

    # everything else basically
    else:
        log(f'{ctx.author} {ctx.author.id} issued a command error: {error}', level=ERROR)
        await ctx.reply(embed=UNKNOWN_ERROR_EMBED, ephemeral=True)


# connection events

@bot.event
async def on_ready():
    log('Ready!')


@bot.event
async def on_connect():
    log('Connected!')


# syncing tree

@bot.command(aliases=['st'])
async def synctree(ctx):
    '''
    Syncs slash command tree.
    '''
    if ctx.author.id not in ADMINS: return

    log(f'{ctx.author.id} requested tree syncing')
    embed = discord.Embed(
        title=f'Syncing...', color=discord.Color.yellow()
    )
    msg = await ctx.reply(embed=embed)
    
    synced = await bot.tree.sync()
    log(f'{ctx.author.id} synced tree with {len(synced)} commands', level=SUCCESS)
    embed = discord.Embed(
        title=f'✅ {len(synced)} commands synced!',
        color=discord.Color.green()
    )
    await msg.edit(embed=embed)


# adding reactions

def get_post_embed(post:api.Post, message:discord.Message, reactions:int) -> discord.Embed:
    '''
    Returns a Discord embed to send.
    '''
    # description
    text = utils.shorten_string(message.content, 512, False)
    text += f'\n\n-# Sent in {message.channel.mention} at <t:{int(message.created_at.timestamp())}>'

    at = len(message.attachments)
    if at > 0:
        text += f'\n-# {at} attachment{"s" if at > 1 else ""}'

    em = len(message.embeds)
    if em > 0:
        text += f'\n-# {em} embed{"s" if em > 1 else ""}'

    # embed
    embed = discord.Embed(
        title=f'{reactions} 🥟',
        description=text,
        color=discord.Color.green()
    )
    # image
    if len(message.attachments) > 0 and message.attachments[0].width != None:
        embed.set_image(url=message.attachments[0].url)

    # author
    embed.set_author(
        name=message.author.name,
        icon_url=message.author.display_avatar.url\
            if message.author.display_avatar else None
    )
    # footer
    embed.set_footer(text=f'Dumplingpost #{post.number}')

    return embed


async def edit_post(
    post:api.Post, message:discord.Message,
    reactions:int, channel:discord.TextChannel
):
    '''
    Edits an already existing post.
    ''' 
    embed = get_post_embed(post, message, reactions)
    message = await channel.fetch_message(post.post_id)
    await message.edit(embed=embed)


@bot.event
async def on_raw_message_edit(payload:discord.RawMessageUpdateEvent):
    '''
    Message edited.
    '''
    # checking if guild is set up correctly
    if payload.guild_id not in mg.guilds:
        return
    
    guild = mg.guilds[payload.guild_id]

    if guild.db_channel == None:
        return
    
    # getting message
    mguild = bot.get_guild(payload.guild_id)
    message = await mguild.get_channel(payload.channel_id).fetch_message(payload.message_id)
    
    # checking if already sent
    post = guild.get_post(payload.message_id)
    db_channel = mguild.get_channel(guild.db_channel)

    if post != None:
        try:
            await edit_post(post, message, post.reactions, db_channel)
        except Exception as e:
            log(f'Error while editing post: {e}', level=ERROR)
        return


@bot.event
async def on_raw_reaction_remove(payload:discord.RawReactionActionEvent):
    '''
    Removed reaction from a message.
    '''
    # checking if guild is set up correctly
    if payload.guild_id not in mg.guilds:
        return
    
    guild = mg.guilds[payload.guild_id]

    if guild.db_channel == None:
        return

    # checking reaction
    channel = bot.get_guild(payload.guild_id).get_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)

    for i in message.reactions:
        if i.emoji == '🥟':
            reaction: discord.Reaction = i
            break
    else:
        return
    
    # checking if already sent
    post = guild.get_post(payload.message_id)
    db_channel = bot.get_guild(payload.guild_id).get_channel(guild.db_channel)

    if post != None:
        if reaction.count == post.reactions:
            return
        
        try:
            await edit_post(post, message, reaction.count, db_channel)
        except Exception as e:
            log(f'Error while editing post: {e}', level=ERROR)
        mg.set_post_reactions(guild.id, post.number, reaction.count)
        return


@bot.event
async def on_raw_reaction_add(payload:discord.RawReactionActionEvent):
    '''
    Added reaction to a message.
    '''
    # checking if guild is set up correctly
    if payload.guild_id not in mg.guilds:
        return
    
    guild = mg.guilds[payload.guild_id]

    if guild.db_channel == None:
        return

    # checking if dumpling
    if payload.emoji.is_unicode_emoji() and payload.emoji.name != '🥟':
        return
    
    # checking if it's not a bot's message
    for i in guild.sent_posts:
        if i.post_id == payload.message_id:
            return
    
    # checking reaction
    channel = bot.get_guild(payload.guild_id).get_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)

    for i in message.reactions:
        if i.emoji == '🥟':
            reaction: discord.Reaction = i
            break
    else:
        return
    
    # checking amount
    if reaction.count < guild.reactions:
        return
    
    # checking if already sent
    post = guild.get_post(payload.message_id)
    db_channel = bot.get_guild(payload.guild_id).get_channel(guild.db_channel)

    if post != None:
        if reaction.count == post.reactions:
            return
        
        try:
            await edit_post(post, message, reaction.count, db_channel)
        except Exception as e:
            log(f'Error while editing post: {e}', level=ERROR)
        mg.set_post_reactions(guild.id, post.number, reaction.count)
        return
    
    # adding post
    post = mg.send_post(
        payload.guild_id, payload.message_id
    )

    # sending post
    embed = get_post_embed(post, message, reaction.count)

    view = discord.ui.View()
    button = discord.ui.Button(
        label='Go to message',
        url=message.jump_url
    )
    view.add_item(button)

    message = await db_channel.send(embed=embed, view=view)
    mg.set_post_id(guild.id, post.number, message.id)


# ping

@bot.hybrid_command(
    name='ping',
    description='View current bot ping/latency.',
)
async def ping(ctx:commands.Context):
    '''
    A ping command.
    '''
    ping = round(bot.latency*1000)

    embed = discord.Embed(
        title='🏓 Pong!',
        color=discord.Color.green(),
        description=f'{ping} ms'
    )
    await ctx.reply(embed=embed)


# managing channels

@bot.hybrid_command(
    name='set-channel',
    description='Set a new dumplingbard channel.',
    aliases=['setchannel','set_channel']
)
@discord.app_commands.describe(
    channel='New dumplingboard channel.'
)
@commands.has_permissions(administrator=True)
async def set_channel(ctx:commands.Context, channel:discord.TextChannel):
    mg.check_guild(ctx.guild.id)

    if channel.id == mg.guilds[ctx.guild.id].db_channel:
        embed = discord.Embed(
            title='❌ Oops!',
            color=discord.Color.red(),
            description='Dumplingboard is already set to this channel.'
        )
        await ctx.reply(embed=embed)
        return

    mg.set_channel(ctx.guild.id, channel.id)

    embed = discord.Embed(
        title='🥟 Success!',
        color=discord.Color.green(),
        description=f'Dumplingboard set to channel {channel.mention}'
    )
    await ctx.reply(embed=embed)


@bot.hybrid_command(
    name='remove-channel',
    description='Removes current dumplingboard channel.',
    aliases=['removechannel','remove_channel']
)
@commands.has_permissions(administrator=True)
async def remove_channel(ctx:commands.Context):
    mg.check_guild(ctx.guild.id)

    if mg.guilds[ctx.guild.id].db_channel == None:
        embed = discord.Embed(
            title='❌ Oops!',
            color=discord.Color.red(),
            description='Dumplingboard is already not on this server.'
        )
        await ctx.reply(embed=embed)
        return

    mg.remove_channel(ctx.guild.id)

    embed = discord.Embed(
        title='🥟 Success!',
        color=discord.Color.green(),
        description=f'Dumplingboard channel is removed.'
    )
    await ctx.reply(embed=embed)


@bot.hybrid_command(
    name='set-reactions',
    description='Changes the amount of dumplings required to send a message into a dumplingboard.',
    aliases=['setreactions','set_reactions']
)
@discord.app_commands.describe(
    amount='New amount of reactions required'
)
@commands.has_permissions(administrator=True)
async def set_reactions(ctx:commands.Context, amount:int):
    mg.check_guild(ctx.guild.id)

    if mg.guilds[ctx.guild.id].reactions == amount:
        embed = discord.Embed(
            title='❌ Oops!',
            color=discord.Color.red(),
            description=f'It\'s already set up to be **{amount}** reactions.'
        )
        await ctx.reply(embed=embed)
        return
    
    if amount < 1:
        embed = discord.Embed(
            title='❌ Oops!',
            color=discord.Color.red(),
            description=f'The amount of reactions must be at least **1**.'
        )
        await ctx.reply(embed=embed)
        return

    mg.set_reactions(ctx.guild.id, amount)

    embed = discord.Embed(
        title='🥟 Success!',
        color=discord.Color.green(),
        description=f'Amount required to send a message into a dumplingboard is now **{amount}**.'
    )
    await ctx.reply(embed=embed)


## RUNNING BOT
bot.run(TOKEN)