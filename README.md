# turieowpq

This repo stores the code for qpwoeirut's spambot named turieowpq (turi for short).
Turi can also play music, sort of.
It's been personalized for my own preferences and might not work too well if multiple people use it at once.

The `.env` file isn't in the repository since it's secret.

## Hosting
This bot is currently hosted on Heroku's free tier, which is nonideal since it goes down for around the last week of each month.
The buildpacks for ffmpeg (https://github.com/jonathanong/heroku-buildpack-ffmpeg-latest.git) and opus (https://github.com/xrisk/heroku-opus.git) need to be added in order for the bot to run.

## TODOs
* Add shuffling
  * Investigate not using `asyncio.Queue`
* Add download caches
* Make turi disconnect when taken offline
  * Check that the cleanup works properly
* Add seek commands
* Add current time to nowplaying
* Improve queue embed (pagination?!)
  * Also add loop settings
* Add stats for what music I listen to
* Figure out the `HTTP error 403 Forbidden`s

## References
* The spammer is loosely based on https://medium.com/better-programming/coding-a-discord-bot-with-python-64da9d6cade7
* The code for the music is based on https://github.com/Rapptz/discord.py/blob/v1.7.3/examples/basic_voice.py and https://gist.github.com/EvieePy/7822af90858ef65012ea500bcecf1612


## Invite Link
https://discord.com/api/oauth2/authorize?client_id=703505605746491482&permissions=2048&scope=bot
