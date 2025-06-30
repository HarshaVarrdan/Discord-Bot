import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import yt_dlp
import os

TOKEN = "MTEwNzI0NzM2OTgxMDEwNDM1MQ.G5OVmI.OxsFHKE8ghRGLpKkMrk4sdSdq33YvaBCJQVoJM"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

vc_clients = {}

YDL_OPTIONS = {
    'format': 'bestaudio/best',
    'quiet': True,
    'extract_flat': False,
    'noplaylist': True,
    'default_search': 'auto',
}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands.")
    except Exception as e:
        print(e)

@bot.tree.command(name="play", description="Play music from YouTube or Spotify")
@app_commands.describe(url="YouTube or Spotify URL")
async def play(interaction: discord.Interaction, url: str):
    await interaction.response.defer()

    if interaction.user.voice is None:
        await interaction.followup.send("Join a voice channel first.")
        return

    voice_channel = interaction.user.voice.channel

    # Connect if not already
    if interaction.guild.id not in vc_clients:
        vc_clients[interaction.guild.id] = await voice_channel.connect()
    elif not vc_clients[interaction.guild.id].is_connected():
        vc_clients[interaction.guild.id] = await voice_channel.connect()

    vc = vc_clients[interaction.guild.id]

    # Handle Spotify links
    if "open.spotify.com" in url:
        await interaction.followup.send("Spotify links are supported only via YouTube proxy. Please paste a song name or use a YouTube link.")
        return

    with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            if "entries" in info:
                info = info["entries"][0]
            audio_url = info['url']
            title = info.get('title', 'Unknown title')
        except Exception as e:
            await interaction.followup.send(f"Error extracting audio: {e}")
            return

    if vc.is_playing():
        vc.stop()

    vc.play(discord.FFmpegPCMAudio(audio_url, **FFMPEG_OPTIONS))
    await interaction.followup.send(f"Now playing: **{title}**")

@bot.tree.command(name="disconnect", description="Disconnect the bot from voice")
async def disconnect(interaction: discord.Interaction):
    vc = vc_clients.get(interaction.guild.id)
    if vc and vc.is_connected():
        await vc.disconnect()
        del vc_clients[interaction.guild.id]
        await interaction.response.send_message("Disconnected from the voice channel.")
    else:
        await interaction.response.send_message("I'm not in a voice channel.")

@bot.tree.command(name="stop", description="Stop the current song")
async def stop(interaction: discord.Interaction):
    vc = vc_clients.get(interaction.guild.id)
    if vc and vc.is_playing():
        vc.stop()
        await interaction.response.send_message("Stopped the music.")
    else:
        await interaction.response.send_message("No music is playing.")

bot.run(TOKEN)
