import discord

PREFIXES = '!'
ADMINS = [698457845301248010, 920449990869004298]

LOG_FILE = 'log.txt'
DATA_FILE = 'data.json'


UNKNOWN_ERROR_EMBED = discord.Embed(
    description='❌ An unknown error occured. Try again.',
    color=discord.Color.red(),
)
ARGS_REQUIRED_EMBED = discord.Embed(
    description='❌ Not enough arguments',
    color=discord.Color.red()
)
MISSING_PERMS_EMBED = discord.Embed(
    description='❌ No permissions',
    color=discord.Color.red()
)
BOT_MISSING_PERMS_EMBED = discord.Embed(
    description='😔 I hav no permissions',
    color=discord.Color.red()
)
UNKNOWN_CHANNEL_EMBED = discord.Embed(
    description='❌ Don\'t know that channel',
    color=discord.Color.red()
)
UNKNOWN_USER_EMBED = discord.Embed(
    description='❌ Don\'t know that user',
    color=discord.Color.red()
)