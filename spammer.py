import itertools
import random

import discord

# WORDS = ["scary", "lel", "lol", "aiya", "bruh", "breh", "oop", "<:notlikeduck:764579516755738664>",
#          "<:tourist_mad:764579517515300914>", "<:confus:764579516755738664>", "<:foncus:766364807732527114>"]
WORDS = [
    "scary", "terrible", "rude", "lol", "aiya", "bruh", "oop", "true", "ok", "cool", "hi", "hehe", "gah", "issoke",
    "yes", "epic", "popping", "fair", "omg", ":0", "i-", "indeed", "anyway", "funny", "ugh", "idk",
    "<:notlikeduck:764579516755738664>", "<:confus:764579516755738664>", "<:foncus:766364807732527114>",
    ":clown:", "<:lemondamage:928558941330358272>", "<:lemonthink:928558940210466836>"
]
EMOTES = [":notlikeduck:", ":tourist_mad:", ":confus:", ":foncus:"]
WORD_CHANCE = int(len(WORDS) * 1.25)
COWWIN = ["galen colin", "colin galen", "calen golin", "golin calen", "cowwin", "galen", "colin", "calin golin"]
COWWIN.extend([x.replace(' ', '_') for x in COWWIN if ' ' in x])
COLIN_ORZ = ["try again", "try another time"]


def is_hm(text):
    return set(text) <= set("hm") and len(text) >= 2


async def spam(message):
    # with open("log.txt", 'a') as f:
    #     print(f"{message.author} said: {message.content}", file=f)
    msg = message.content.lower()
    if message.author.id == 145266128363585536 and any([msg in orz for orz in COLIN_ORZ]):
        reply = random.choice(COWWIN)
    elif any([emote in msg for emote in itertools.chain(EMOTES, WORDS)]):
        # print("word matched", file=f)
        idx = random.randint(0, WORD_CHANCE - 1)
        if idx < len(WORDS):
            reply = WORDS[idx]
        else:
            reply = message.content
    elif is_hm(msg):
        # print("hm matched", file=f)
        if random.randint(1, 10) == 1:
            reply = "yumm"
        else:
            reply_size = min(500, len(message.content))
            reply = ""
            if random.randint(0, 1) == 0:
                reply += 'm' * random.randint(1, reply_size // 2)
            reply += 'h'
            reply += 'm' * random.randint(1, reply_size)
    elif "sir" in msg:
        # print("sir matched", file=f)
        reply = f"hello {message.author.mention} sir"
    elif "sad" in msg:
        # print("sad matched, file=f)
        reply = f"{random.choice(['so', 'very'])} sad!"
    elif 'q' in msg and random.randint(1, 3) == 1:
        # print("q matched", file=f)
        reply = "q is the best letter!"
    elif random.randint(1, 5) == 1:
        # print("random word", file=f)
        reply = random.choice(WORDS)
    elif ' ' not in message.content and ':' not in message.content and random.randint(1, 8) == 1:
        reply = message.content[::-1]
    elif ' ' in message.content and random.randint(1, 10) == 1:
        words = message.content.split()
        words.reverse()
        reply = ' '.join(words)
    else:
        return
    # print(f"sent {reply}", file=f)
    await message.channel.send(reply, allowed_mentions=discord.AllowedMentions.none())
