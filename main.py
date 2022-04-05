# SOLVE aiohttp.client_exceptions.ClientConnectorCertificateError
# https://stackoverflow.com/questions/59411362/ssl-certificate-verify-failed-certificate-verify-failed-unable-to-get-local-i
import discord
from discord.ext import commands

from get_token import DISCORD_TOKEN
from MusicCog import MusicCog
from spammer import spam

client = commands.Bot(command_prefix=commands.when_mentioned_or("turi "),
                      description='turieowpq', allowed_mentions=discord.AllowedMentions(everyone=False, roles=False))


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
    # https://stackoverflow.com/questions/49331096/why-does-on-message-stop-commands-from-working


if __name__ == '__main__':
    client.add_cog(MusicCog(client))
    client.run(DISCORD_TOKEN)
