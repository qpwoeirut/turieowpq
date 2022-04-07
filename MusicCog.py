import discord
from discord.ext import commands

import asyncio
import itertools
import traceback

from MusicPlayer import MusicPlayer, music_log, MUSIC_LOGS_FILENAME
from YTDLSource import YTDLSource
from taylor_swift import TAYLOR_SWIFT


class VoiceConnectionError(commands.CommandError):
    """Custom Exception class for connection errors."""


class InvalidVoiceChannel(VoiceConnectionError):
    """Exception for cases of invalid Voice Channels."""


class MusicCog(commands.Cog):
    """Music related commands."""

    __slots__ = ('bot', 'player')

    def __init__(self, bot):
        self.bot = bot
        self.player = None

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """A local error handler for all errors arising from commands in this cog."""
        try:
            if isinstance(error, commands.NoPrivateMessage):
                await ctx.send('This command can not be used in DMs')
            elif isinstance(error, InvalidVoiceChannel):
                await ctx.send('invalid voice channel!')
            elif isinstance(error, commands.CommandNotFound):
                await ctx.send('invalid command!')
            else:
                music_log(f'Ignoring exception in command {ctx.command}:')
                with open(MUSIC_LOGS_FILENAME, "a") as log_file:
                    traceback.print_exception(type(error), error, error.__traceback__, file=log_file)

                await ctx.send(f"Error: {error}", allowed_mentions=discord.AllowedMentions.none())
        except discord.HTTPException:
            pass

    def get_player(self, ctx):
        """Retrieve the music player, or generate one."""
        if self.player is None:
            self.player = MusicPlayer(ctx)
        return self.player

    @commands.guild_only()
    @commands.command(name='join', aliases=['connect'])
    async def join(self, ctx, *, channel: discord.VoiceChannel = None):
        """join a voice channel
        Parameters
        ------------
        ctx: context
        channel: discord.VoiceChannel [Optional]
            The channel to connect to. If a channel is not specified, an attempt to join the voice channel you are in
            will be made.
        This command also handles moving the bot to different channels.
        """
        music_log(f"joining voice channel {channel}")
        if not channel:
            try:
                channel = ctx.author.voice.channel
            except AttributeError:
                raise InvalidVoiceChannel('No channel to join. Please either specify a valid channel or join one.')

        vc = ctx.voice_client

        if vc:
            if vc.channel.id == channel.id:
                return
            try:
                await vc.move_to(channel)
            except asyncio.TimeoutError:
                raise VoiceConnectionError(f'Moving to channel: <{channel}> timed out.')
        else:
            try:
                await channel.connect()
            except asyncio.TimeoutError:
                raise VoiceConnectionError(f'Connecting to channel: <{channel}> timed out.')

    async def _play(self, ctx, search: str):
        player = self.get_player(ctx)

        # each source is a dict which will be used later to regather the stream
        sources = await YTDLSource.create_source(ctx, search, loop=self.bot.loop)
        for source in sources:
            await player.queue.put(source)

    @commands.guild_only()
    @commands.command(name='play')
    async def play(self, ctx, *, search: str):
        """Request a song and add it to the queue.
        This command attempts to join a valid voice channel if the bot is not already in one.
        Uses YTDL to automatically search and retrieve a song.
        Parameters
        ------------
        ctx: context
        search: str [Required]
            The song to search and retrieve using YTDL. This could be a simple search, an ID or URL.
        """
        music_log(f"playing from search: {search}")

        await ctx.trigger_typing()

        if not ctx.voice_client:
            await ctx.invoke(self.join)

        await self._play(ctx, search)

    @commands.guild_only()
    @commands.command(name="taylor_swift", aliases=["ts", "taylor", "preset", "play_preset"])
    async def taylor_swift(self, ctx, *, search: str):
        music_log(f"playing from taylor swift: {search}")

        if search.lower() not in TAYLOR_SWIFT.keys():
            await ctx.send("Search not found!")
            return

        await ctx.trigger_typing()

        if not ctx.voice_client:
            await ctx.invoke(self.join)

        await self._play(ctx, TAYLOR_SWIFT[search])

    @commands.guild_only()
    @commands.command(name='pause')
    async def pause(self, ctx):
        """Pause the currently playing song."""
        vc = ctx.voice_client

        if not vc or not vc.is_playing():
            return await ctx.send('I am not currently playing anything!')
        elif vc.is_paused():
            return

        vc.pause()
        await ctx.send(f'**`{ctx.author}`**: Paused the song!')

    @commands.guild_only()
    @commands.command(name='resume')
    async def resume(self, ctx):
        """Resume the currently paused song."""
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            return await ctx.send('I am not currently playing anything!')
        elif not vc.is_paused():
            return

        vc.resume()
        await ctx.send(f'**`{ctx.author}`**: Resumed the song!')

    @commands.guild_only()
    @commands.command(name='skip')
    async def skip(self, ctx):
        """Skip the song."""
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            return await ctx.send('I am not currently playing anything!')

        if vc.is_paused():
            pass
        elif not vc.is_playing():
            return

        vc.stop()
        await ctx.send(f'**`{ctx.author}`**: Skipped the song!')

    @commands.guild_only()
    @commands.command(name="loop", aliases=["qloop", "loopq", "loop_queue", "loopqueue"])
    async def loop_queue(self, ctx):
        player = self.get_player(ctx)
        player.loop_queue = not player.loop_queue
        await ctx.send(f"Looping queue **{'enabled' if player.loop_queue else 'disabled'}**!")

    @commands.guild_only()
    @commands.command(name="loop_song", aliases=["sloop", "loops", "loopsong"])
    async def loop_song(self, ctx):
        player = self.get_player(ctx)
        player.loop_song = not player.loop_song
        await ctx.send(f"Looping song **{'enabled' if player.loop_song else 'disabled'}**!")

    @commands.guild_only()
    @commands.command(name='queue', aliases=['q', 'playlist'])
    async def queue_info(self, ctx):
        """Retrieve a basic queue of upcoming songs."""
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            return await ctx.send('I am not currently connected to voice!')

        player = self.get_player(ctx)
        if player.queue.empty():
            return await ctx.send('There are currently no more queued songs.')

        # Grab up to 10 entries from the queue...
        upcoming = list(itertools.islice(player.queue._queue, 0, 10))

        fmt = '\n'.join(f'**`{_["title"]}`**' for _ in upcoming)
        embed = discord.Embed(title=f'Next {len(upcoming)} songs (out of {player.queue.qsize()})', description=fmt)

        await ctx.send(embed=embed)

    @commands.guild_only()
    @commands.command(name='now_playing', aliases=['np', "nowplaying", 'current', 'currentsong', 'playing'])
    async def now_playing(self, ctx):
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
    async def change_volume(self, ctx, *, volume: float):
        """Change the player volume.
        Parameters
        ------------
        ctx: context
        volume: float or int [Required]
            The volume to set the player to in percentage. This must be between 1 and 100.
        """
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            await ctx.send('I am not currently connected to voice!')
            return

        if not 1 <= volume <= 100:
            await ctx.send('Volume should be between 1 and 100')
            return

        player = self.get_player(ctx)

        if vc.source:
            vc.source.volume = volume / 100

        player.volume = volume / 100
        await ctx.send(f'**`{ctx.author}`**: Set the volume to **{volume}%**')

    @commands.guild_only()
    @commands.command(name="disconnect", aliases=["dc", "stop", "leave", "bye"])
    async def disconnect(self, ctx):
        """Stop the currently playing song and destroy the player.
        """
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            return await ctx.send('I am not currently playing anything!')

        await self.cleanup(ctx.guild)

    async def cleanup(self, guild):
        try:
            await guild.voice_client.disconnect()
        except AttributeError:
            pass
        self.player = None

    @commands.command(name="dump_logs")
    async def dump_logs(self, ctx):
        with open(MUSIC_LOGS_FILENAME) as log_file:
            logs = log_file.read()
        await ctx.send(f"```\n{logs[-4990:]}\n```")
