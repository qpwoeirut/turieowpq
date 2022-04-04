# https://medium.com/better-programming/coding-a-discord-bot-with-python-64da9d6cade7


# SOLVE aiohttp.client_exceptions.ClientConnectorCertificateError
# https://stackoverflow.com/questions/59411362/ssl-certificate-verify-failed-certificate-verify-failed-unable-to-get-local-i

import discord

from get_token import DISCORD_TOKEN
from spammer import spam

client = discord.Client()


@client.event
async def on_ready():
    for guild in client.guilds:
        print(f"- {guild.id} (name: {guild.name})")


@client.event
async def on_message(message):
    if message.author.bot:
        return
    await spam(message)


client.run(DISCORD_TOKEN)
