# SOLVE aiohttp.client_exceptions.ClientConnectorCertificateError
# https://stackoverflow.com/questions/59411362/ssl-certificate-verify-failed-certificate-verify-failed-unable-to-get-local-i
import asyncio
import discord
from discord.ext import commands

from MusicCog import MusicCog
from get_token import DISCORD_TOKEN
from spammer import spam

client = commands.Bot(
    command_prefix=commands.when_mentioned_or("turi "),
    description='turieowpq',
    allowed_mentions=discord.AllowedMentions.none(),
    # intents=discord.Intents(message_content=True, messages=True, voice_states=True, guilds=True)
    intents=discord.Intents().all()
)


@client.event
async def on_ready():
    print(f"Logged in as {client.user} with id {client.user.id}")
    for guild in client.guilds:
        print(f"- {guild.id} (name: {guild.name})")


@client.event
async def on_message(message):
    if message.author.bot:  # don't reply to bots
        return

    await spam(message)

    await client.process_commands(message)


async def main():
    await client.add_cog(MusicCog(client))
    async with client:
        await client.start(DISCORD_TOKEN)


if __name__ == '__main__':
    asyncio.run(main())
