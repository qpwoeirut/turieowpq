import asyncio
import os
from datetime import datetime

from async_timeout import timeout

from YTDLSource import YTDLSource


os.mkdir("logs")
MUSIC_LOGS_FILENAME = "logs/music_logs.txt"
with open(MUSIC_LOGS_FILENAME, "w"):  # clear file
    pass


def music_log(*items):
    with open(MUSIC_LOGS_FILENAME, "a") as log_file:
        print(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), *items, file=log_file)


class MusicPlayer:
    """A class which is assigned to each guild using the bot for music.
    When the bot disconnects from the vc its instance will be destroyed.
    """

    __slots__ = ('bot', '_guild', '_channel', '_cog', 'queue', 'next', 'current', 'volume', 'loop_song', 'loop_queue')

    def __init__(self, ctx):
        self.bot = ctx.bot
        self._guild = ctx.guild
        self._channel = ctx.channel
        self._cog = ctx.cog

        self.queue = asyncio.Queue()
        self.next = asyncio.Event()

        self.volume = .5
        self.current = None

        self.loop_song = False
        self.loop_queue = False

        ctx.bot.loop.create_task(self.player_loop())

    async def player_loop(self):
        await self.bot.wait_until_ready()

        while not self.bot.is_closed():
            self.next.clear()

            if self.current is None or self.loop_song is False:
                try:
                    # Wait for the next song. If we timeout cancel the player and disconnect...
                    async with timeout(5 * 60):  # 5 minutes
                        source = await self.queue.get()
                except asyncio.TimeoutError:
                    music_log("Timed out while waiting for next song in queue, disconnecting")
                    return self.destroy(self._guild)

                if not isinstance(source, YTDLSource):
                    # Source was probably a stream (not downloaded)
                    # So we should regather to prevent stream expiration
                    try:
                        self.current = await YTDLSource.regather_stream(source, loop=self.bot.loop)
                    except Exception as e:
                        await self._channel.send(f'There was an error processing your song.\n'
                                                 f'```css\n[{e}]\n```')
                        continue

                self.current.volume = self.volume
            else:
                try:
                    self.current = await YTDLSource.regather_stream(source, loop=self.bot.loop)
                except Exception as e:
                    await self._channel.send(f'There was an error processing your song.\n'
                                             f'```css\n[{e}]\n```')
                    continue

            self._guild.voice_client.play(self.current, after=lambda _: self.bot.loop.call_soon_threadsafe(self.next.set))
            await self._channel.send(f'**Now Playing:** `{self.current.title}` requested by `{self.current.requester}`')
            await self.next.wait()

            if self.loop_queue and not self.loop_song:
                await self.queue.put(source)

            # clean up ffmpeg process
            self.current.cleanup()

    def destroy(self, guild):
        """Disconnect and cleanup the player."""
        return self.bot.loop.create_task(self._cog.cleanup(guild))
