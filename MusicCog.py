# based on https://github.com/Rapptz/discord.py/blob/v2.2.2/examples/basic_voice.py

import logging
import traceback

import discord
from discord.ext import commands
from discord.ext.commands import Context

from MusicPlayer import MusicPlayer, SongInfo
from YTDLSource import YTDLSource
from preset import TAYLOR_SWIFT, THE_SCORE


class VoiceConnectionError(commands.CommandError):
    """Custom Exception class for connection errors."""


class InvalidVoiceChannel(VoiceConnectionError):
    """Exception for cases of invalid Voice Channels."""


class MusicCog(commands.Cog):
    """Music related commands."""

    __slots__ = ('bot', 'player')

    def __init__(self, bot):
        self.bot = bot
        self._player = None

    @commands.Cog.listener()
    async def on_command_error(self, ctx: Context, error):
        """A local error handler for all errors arising from commands in this cog"""
        try:
            if isinstance(error, commands.NoPrivateMessage):
                await ctx.send('This command can not be used in DMs.')
            elif isinstance(error, InvalidVoiceChannel):
                await ctx.send('Invalid voice channel!')
            elif isinstance(error, commands.CommandNotFound):
                await ctx.send('Invalid command!')
            else:
                logging.exception(''.join(traceback.format_exception(type(error), error, error.__traceback__)))
                await ctx.channel.send(f"Error:\n```css\n[{error}]\n```")
        except discord.HTTPException:
            pass

    def get_player(self, ctx: Context):
        """Retrieve the music player, or generate one"""
        if self._player is None:
            self._player = MusicPlayer(ctx)
        return self._player

    @commands.guild_only()
    @commands.command(name='join', aliases=['connect'])
    async def join(self, ctx: Context, *, channel: discord.VoiceChannel = None):
        await self._join(ctx, channel=channel)

    async def _play(self, ctx: Context, search: str):
        player = self.get_player(ctx)

        # each source is a dict which will be used later to regather the stream
        sources = await YTDLSource.create_source(ctx, search, loop=self.bot.loop)
        for source in sources:
            player.add_song(SongInfo(url=source['url'], requester=ctx.author, title=source['title']))

    @commands.guild_only()
    @commands.command(name='play')
    async def play(self, ctx: Context, *, search: str):
        """Request a song and add it to the queue.
        This command attempts to join a valid voice channel if the bot is not already in one.
        Uses YTDL to automatically search and retrieve a song.
        Parameters
        ------------
        ctx: context
        search: str [Required]
            The song to search and retrieve using YTDL. This could be a simple search, an ID or URL.
        """
        logging.info(f"playing from search: {search}")

        await self._play(ctx, search)

    @commands.guild_only()
    @commands.command(name="preset", aliases=["ts", "taylor", "the_score", "taylor_swift"])
    async def preset(self, ctx: Context, *, search: str):
        """Play a song or playlist from a preset list
        Parameters
        ------------
        ctx: context
        search: str [Required]
            The song to retrieve from a lookup list in preset.py (case insensitive)
        """
        logging.info(f"playing from preset: {search}")

        presets = TAYLOR_SWIFT | THE_SCORE

        if search.lower() in presets.keys():
            return await self._play(ctx, presets[search])
        elif all([s in presets or s.replace('_', ' ') in presets for s in search.split()]):
            for s in search.split():
                s = presets[s] if s in presets else presets[s.replace('_', ' ')]
                await self._play(ctx, s)
            return
        return await ctx.send("Search not found!")


    @commands.guild_only()
    @commands.command(name='pause')
    async def pause(self, ctx: Context):
        """Pause the currently playing song"""
        vc = ctx.voice_client

        if not vc or not vc.is_playing():
            return await ctx.send('I am not currently playing anything!')
        elif vc.is_paused():
            return

        vc.pause()
        await ctx.send(f'**`{ctx.author}`**: Paused')

    @commands.guild_only()
    @commands.command(name='resume')
    async def resume(self, ctx: Context):
        """Resume the currently paused song"""
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            return await ctx.send('I am not currently playing anything!')
        elif not vc.is_paused():
            return

        vc.resume()
        await ctx.send(f'**`{ctx.author}`**: Resumed')

    @commands.guild_only()
    @commands.command(name='skip')
    async def skip(self, ctx: Context, *, index: int = 0):
        """Skip the song"""
        if not (ctx.voice_client.is_paused() or ctx.voice_client.is_playing()):
            await ctx.send("Not currently playing anything!")
            return
        if index != 0:
            return await self.remove(ctx, index)

        player = self.get_player(ctx)
        skipped_title = player.cur_source.title
        player.skip()
        await ctx.send(f'**`{ctx.author}`**: Skipped `{skipped_title}`')

    @commands.guild_only()
    @commands.command(name='remove', aliases=["pop", "delete"])
    async def remove(self, ctx: Context, index: int):
        """Removes a song from the queue"""

        player = self.get_player(ctx)
        deleted = player.delete_song(index - 1)
        await ctx.send(f"**`{ctx.author}`**: Removed `{deleted.title}`")

    @commands.guild_only()
    @commands.command(name='shuffle')
    async def shuffle(self, ctx: Context):
        """Shuffles queue"""

        player = self.get_player(ctx)
        player.shuffle_songs()
        await ctx.send(f"**`{ctx.author}`**: Shuffled queue")

    @commands.guild_only()
    @commands.command(name="loop", aliases=["qloop", "loopq", "loop_queue", "loopqueue"])
    async def loop_queue(self, ctx: Context):
        """Add a song to the end of the queue when it ends or is skipped"""
        player = self.get_player(ctx)
        player.loop_queue = not player.loop_queue
        await ctx.send(f"**`{ctx.author}`**: Looping queue **{'enabled' if player.loop_queue else 'disabled'}**")

    @commands.guild_only()
    @commands.command(name="loop_song", aliases=["sloop", "loops", "loopsong"])
    async def loop_song(self, ctx: Context):
        """Loop the current song"""
        player = self.get_player(ctx)
        player.loop_song = not player.loop_song
        await ctx.send(f"**`{ctx.author}`**: Looping song **{'enabled' if player.loop_song else 'disabled'}**")

    @commands.guild_only()
    @commands.command(name='queue', aliases=['q', 'playlist'])
    async def get_queue(self, ctx: Context, *, page: int = 1):
        """Retrieve a basic queue of upcoming songs"""
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            return await ctx.send('I am not currently connected to voice!')

        player = self.get_player(ctx)
        if not player.pending.is_set():
            return await ctx.send('There are currently no more queued songs.')

        page_count = (player.queue_size() // 10) + 1
        if page > page_count:
            return await ctx.send(f"There are only {page_count} pages.")
        if page <= 0:
            return await ctx.send("Pages are 1-indexed.")

        start = (page - 1) * 10
        upcoming = player.get_songs(10, start)
        desc = '\n'.join(f"{start + i + 1}. {song.title}" for i, song in enumerate(upcoming))
        embed = discord.Embed(
            title=f"Page {page} of {page_count} ({player.queue_size()} total)",
            description=f"```{desc}```"
        )

        await ctx.send(embed=embed)

    @commands.guild_only()
    @commands.command(name='now_playing', aliases=['np', "nowplaying", 'current', 'currentsong', 'playing'])
    async def now_playing(self, ctx: Context):
        """Display information about the currently playing song."""
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            return await ctx.send('I am not currently connected to voice!')

        player = self.get_player(ctx)
        if not player.current:
            return await ctx.send('I am not currently playing anything!')

        current_song_info = f"**Now Playing:** `{vc.source.title}` requested by `{vc.source.requester}`."
        loop_settings_info = f"Looping song: {player.loop_song}. Looping queue: {player.loop_queue}."
        await ctx.send(f"{current_song_info}\n{loop_settings_info}")

    @commands.guild_only()
    @commands.command(name='volume', aliases=['vol'])
    async def volume(self, ctx: Context, *, volume: float):
        """Change the player volume
        Parameters
        ------------
        ctx: context
        volume: float or int [Required]
            The volume to set the player to in percentage. This must be between 1 and 100.
        """

        if not 1 <= volume <= 100:
            await ctx.send('Volume should be between 1 and 100')
            return

        player = self.get_player(ctx)

        if ctx.voice_client.source:  # set volume for current song
            ctx.voice_client.source.volume = volume / 100

        player.volume = volume / 100  # set volume for future songs
        await ctx.send(f'**`{ctx.author}`**: Set the volume to **{volume}%**')

    @commands.guild_only()
    @commands.command(name="disconnect", aliases=["dc", "stop", "leave", "bye"])
    async def disconnect(self, ctx: Context):
        """Stop the currently playing song and destroy the player
        """
        await self.cleanup(ctx.guild)

    @staticmethod
    async def cleanup(guild):
        try:
            await guild.voice_client.disconnect()
            await guild.voice_client.cleanup()
        except AttributeError:
            pass

    @play.before_invoke
    @preset.before_invoke
    async def _join(self, ctx: Context, *, channel: discord.VoiceChannel = None):
        if not channel:
            try:
                channel = ctx.author.voice.channel
            except AttributeError:
                raise InvalidVoiceChannel('No channel to join. Please either specify a valid channel or join one.')

        if ctx.voice_client is not None:
            return await ctx.voice_client.move_to(channel)

        await channel.connect()

    @pause.before_invoke
    @resume.before_invoke
    @skip.before_invoke
    @loop_queue.before_invoke
    @loop_song.before_invoke
    @get_queue.before_invoke
    @now_playing.before_invoke
    @volume.before_invoke
    @disconnect.before_invoke
    async def assert_voice(self, ctx):
        if ctx.voice_client is None:
            raise InvalidVoiceChannel("You are not connected to a voice channel.")

    @commands.command(name="dump_logs")
    async def dump_logs(self, ctx: Context):
        with open("log.txt") as log_file:
            logs = log_file.read()
        await ctx.send(f"```\n{logs[-1990:]}\n```")

    @commands.command(name="ping")
    async def ping(self, ctx: Context):
        await ctx.send(f"Latency: {round(self.bot.latency * 1000)}ms")
