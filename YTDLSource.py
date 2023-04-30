import asyncio
from functools import partial
from typing import Iterable

import discord
import yt_dlp
from discord.ext.commands import Context

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',  # bind to ipv4 since ipv6 addresses cause issues sometimes
    "highwatermark": 1 << 15
}

# https://stackoverflow.com/questions/66070749/how-to-fix-discord-music-bot-that-stops-playing-before-the-song-is-actually-over
# https://stackoverflow.com/questions/50924411/using-ffmpeg-with-python-input-buffer-exhausted-before-end-element-found
ffmpeg_options = {
    'options': '-vn -dn -sn -ignore_unknown',
    "before_options": "-nostdin -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, requester):
        super().__init__(source)
        self.requester = requester

        self.title = data.get('title')

        # YTDL info dicts (data) have other useful information you might want
        # https://github.com/rg3/youtube-dl/blob/master/README.md

    def __getitem__(self, item: str):
        """Allows us to access attributes similar to a dict.
        This is only useful when you are NOT downloading.
        """
        return self.__getattribute__(item)

    @classmethod
    async def create_source(cls, ctx: Context, search: str, *, loop) -> Iterable:
        loop = loop or asyncio.get_event_loop()

        # for playlists, set process=False to get a generator for entries instead of downloading all the info at once
        not_playlist = "youtube.com/playlist" not in search
        if not_playlist:
            search = "ytsearch1:" + search  # only fetch first result to make things faster
        to_run = partial(ytdl.extract_info, url=search, download=False, process=not_playlist)
        data = await loop.run_in_executor(None, to_run)

        if data["extractor"] == "youtube:search":  # search queries return a playlist; we'll pick the first song
            assert "entries" in data, "Expected key 'entries' to exist in returned data from search query"
            data = data["entries"][0]

        # make a list, even if there's only one song, in order to support playlists
        data_list = data["entries"] if "entries" in data else [data]
        song_count = data["playlist_count"] if "playlist_count" in data else 1
        message = f"[Added {data['title']} to the Queue.{'' if song_count == 1 else f'({song_count} songs)'}]"
        await ctx.send(f'```ini\n{message}\n```')

        return data_list

    @classmethod
    async def regather_stream(cls, data, *, loop):
        """Used for preparing a stream, instead of downloading.
        Since YouTube Streaming links expire."""
        loop = loop or asyncio.get_event_loop()
        requester = data['requester']

        to_run = partial(ytdl.extract_info, url=data['url'], download=False)
        regathered_data = await loop.run_in_executor(None, to_run)
        regathered_data["title"] = data["title"]

        return cls(discord.FFmpegPCMAudio(regathered_data['url'], **ffmpeg_options),
                   data=regathered_data, requester=requester)


def main():
    ytdl.extract_info("https://www.youtube.com/playlist?list=PLKwS6yNh-76kw73M6DhBiRwxtNbtKLPEm", download=True)


if __name__ == "__main__":
    main()