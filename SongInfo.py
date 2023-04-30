import discord


class SongInfo:
    def __init__(self, url: str, requester: discord.User | discord.Member, title: str):
        self.url = url
        self.requester = requester
        self.title = title
