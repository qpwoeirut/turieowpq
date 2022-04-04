import os
from dotenv import load_dotenv


load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

assert DISCORD_TOKEN is not None, "Missing Discord Token!"
