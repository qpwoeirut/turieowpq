import asyncio
import itertools
import logging
import traceback
from collections import deque

from async_timeout import timeout
from discord.ext.commands import Context

from SongInfo import SongInfo
from YTDLSource import YTDLSource

logging.basicConfig(
    filename="log.txt", filemode='a',
    datefmt='%Y-%m-%dT%H:%M:%S',
)


class MusicPlayer:
    """A class which is assigned to each guild using the bot for music.
    When the bot disconnects from the vc its instance will be destroyed.
    """

    def __init__(self, ctx: Context):
        self.bot = ctx.bot
        self._guild = ctx.guild
        self._channel = ctx.channel
        self._cog = ctx.cog

        self._queue = deque()
        self.next = asyncio.Event()
        self.pending = asyncio.Event()

        self.volume = .5
        self.current = None

        self.loop_song = False
        self.loop_queue = False

        ctx.bot.loop.create_task(self.player_loop())

    async def player_loop(self):
        await self.bot.wait_until_ready()

        while not self.bot.is_closed():
            self.next.clear()

            try:
                # Wait for the next song. If we timeout cancel the player and disconnect...
                async with timeout(5 * 60):  # 5 minutes
                    await self.pending.wait()
                source = self.pop_song()
            except asyncio.TimeoutError:
                logging.info("Timed out while waiting for next song in queue, disconnecting")
                return self.destroy(self._guild)

            try:
                self.current = await YTDLSource.regather_stream(source, loop=self.bot.loop)
            except Exception as e:
                logging.exception(''.join(traceback.format_exception(type(e), e, e.__traceback__)))
                await self._channel.send(f"Error:\n```css\n[{e}]\n```")
                continue

            self.current.volume = self.volume

            self._guild.voice_client.play(self.current, after=lambda e: self.after(source, e))
            await self._channel.send(f'**Now Playing:** `{self.current.title}` requested by `{self.current.requester}`')
            await self.next.wait()

    async def after(self, source: SongInfo, e: Exception = None):
        if e is not None:
            logging.exception(''.join(traceback.format_exception(type(e), e, e.__traceback__)))
            await self._channel.send(f"Error:\n```css\n[{e}]\n```")

        # clean up ffmpeg process
        self.current.cleanup()

        if self.loop_song:
            self.add_song(source, 0)
        elif self.loop_queue:
            self.add_song(source)
        self.bot.loop.call_soon_threadsafe(self.next.set)

    def add_song(self, song: SongInfo, index=None):
        if index is None:
            self._queue.append(song)
        else:
            self._queue.index(song, index)
        self.pending.set()

    def pop_song(self):
        if self._queue:
            ret = self._queue.popleft()
            if len(self._queue) == 0:
                self.pending.clear()
            return ret
        return None

    def get_songs(self, count: int, start: int = 0) -> list[SongInfo]:
        return list(itertools.islice(self._queue, start, start + count))

    def queue_size(self) -> int:
        return len(self._queue)

    def destroy(self, guild):
        """Disconnect and cleanup the player."""
        return self.bot.loop.create_task(self._cog.cleanup(guild))
