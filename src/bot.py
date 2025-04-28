import discord
from discord.ext import commands
from discord import app_commands
import random
from meme import Meme
from googlesheetsclient import GoogleSheetsClient
from settings import ARTISTS, ACTIVITIES
from typing import Literal, List
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
from pytz import timezone



class DiscordBot:
    def __init__(self, token, guild_id, channel_id):
        self.token = token
        self.guild_id = guild_id
        self.channel_id = channel_id

        intents = discord.Intents.default()
        intents.messages = True

        self.bot = commands.Bot(command_prefix='/', intents=intents)

        # Initialize the scheduler
        self.scheduler = AsyncIOScheduler()
        self.scheduler.add_job(self.send_news, 'cron', day_of_week='mon-fri', hour=9, minute=0, timezone=timezone('Europe/Paris'))


        # Add slash command for afternoon
        @self.bot.tree.command(name="apresmidi", description="Choisissez une option pour l'après-midi")
        @app_commands.describe(option="Options disponibles")
        @app_commands.choices(option=[
            app_commands.Choice(name=activity["name"], value=activity["value"]) for activity in ACTIVITIES
        ])
        async def apresmidi(interaction: discord.Interaction, option: app_commands.Choice[str]):
            await interaction.response.send_message("Ton activité ``" + option.value + "`` a bien été enregistrée pour cet après-midi. Merci !")

        # Update the morning command to use the configurable list
        @self.bot.tree.command(name="matin", description="Choisissez une option pour le matin")
        @app_commands.describe(option="Options disponibles")
        @app_commands.choices(option=[
            app_commands.Choice(name=activity["name"], value=activity["value"]) for activity in ACTIVITIES
        ])
        async def matin(interaction: discord.Interaction, option: app_commands.Choice[str]):
            await interaction.response.send_message("Ton activité ``" + option.value + "`` a bien été enregistrée pour ce matin. Merci !")

        # Add a test command to trigger send_news
        @self.bot.command(name="test", description="Lancer la méthode send_news")
        async def test(interaction: discord.Interaction):
            await self.send_news()


        # Triggers the on_ready function when the bot is ready
        @self.bot.event
        async def on_ready():
            guild = discord.Object(id=self.guild_id)  # Cible le serveur spécifique
            await self.bot.tree.sync()  # Synchronise les commandes pour ce serveur uniquement
            print(f'Bot is ready! Logged in as {self.bot.user}')

            # Start the scheduler in the running event loop
            self.scheduler.start()

    async def send_news(self):

        # Get the current date in the format 'MM/DD/YYYY'
        date = discord.utils.utcnow().strftime('%m/%d/%Y')

        # Add a random meme to the message
        meme_picker = Meme()
        random_meme = meme_picker.PickRandomMeme()

        # Artistes absents
        absent_artists = []
        # Reviews prévues
        reviews = []
        # Reunions
        meetings = []
        # Anniversaires
        birthdays = []

        # Get the row that corresponds to today's date
        sheets = GoogleSheetsClient()
        row = sheets.get_row_by_date(date)


        # Analyse the morning data
        if row[0] != None:

            # Check who is absent in the morning :
            for i in range(3, 12):
                if row[0][i] == "OFF":
                    absent_artists.append("**" + ARTISTS[i]["name"] + "** (matin)")

            events = row[0][2]
            # Split the events into a list
            events = events.split("\n") if events != None else []
            for event in events:
                # Check if the event is a review
                if "review" in event.lower():
                    reviews.append(event)
                # Check if the event is a birthday
                elif "anniv" in event.lower():
                    birthdays.append(event)
                # Check if the event is a meeting
                elif "reu" in event.lower():
                    meetings.append(event)


        # Analyse the afternoon data
        if row[1] != None:

            # Check who is absent in the afternoon :
            for i in range(3, 12):
                if row[1][i] == "OFF":
                    # Check if the artist is already in the list
                    if "**" + ARTISTS[i]["name"] + "** (matin)" not in absent_artists:
                        # If not, add the artist to the list
                        absent_artists.append("**" + ARTISTS[i]["name"] + "** (apres-midi)")

                    else:
                        # Remove the artist from the list
                        absent_artists.remove("**" + ARTISTS[i]["name"] + "** (matin)")
                        absent_artists.append("**" + ARTISTS[i]["name"] + "** (matin & apres-midi)")

            events = row[1][2]
            # Split the events into a list
            events = events.split("\n") if events != None else []

            for event in events:
                # Check if the event is a review
                if "review" in event.lower():
                    reviews.append(event)
                # Check if the event is a birthday
                elif "anniv" in event.lower():
                    birthdays.append(event)
                # Check if the event is a meeting
                elif "reu" in event.lower():
                    meetings.append(event)



        # Create the final message
        message = f'# 📅 Rapport quotidien du {date} \n'
        message += '[Bonjour à tous !](' + random_meme + ') Voici les infos du jour pour bien commencer la journée :\n'
        message += '\n'

        # Add the list of artists
        message += '## 👥 Artistes absents aujourd’hui :\n'
        if len(absent_artists) > 0:
            for artist in absent_artists:
                message += f'- {artist}\n'
        else:
            message += '(Aucun)\n'
        message += '\n'

        # Add the list of Reviews
        message += '## 🎬 Reviews prévues aujourd’hui\n'
        if len(reviews) > 0:
            for review in reviews:
                message += f'- {review}\n'
        else:
            message += '(Aucune)\n'
        message += '\n'

        # Add the list of Meetings
        message += '## 📞 Réunions prévues aujourd’hui\n'
        if len(meetings) > 0:
            for meeting in meetings:
                message += f'- {meeting}\n'
        else:
            message += '(Aucune)\n'
        message += '\n'


        # Add the list of Birthdays
        if len(birthdays) > 0:
            message += '## 🎉 Anniversaire(s)\n'
            for birthday in birthdays:
                message += f'- {birthday}\n'


        message += '\n '
        message += 'Bonne journée à tous et bon taf ! 💪'

        # Send the message
        await self.send_message(message)

    # Send a message
    async def send_message(self, message):
        guild = discord.utils.get(self.bot.guilds, id=self.guild_id)
        if guild:
            channel = discord.utils.get(guild.text_channels, id=self.channel_id)
            if channel:
                await channel.send(message)
            else:
                print('Channel not found')
        else:
            print('Guild not found')

    def run(self):
        self.bot.run(self.token)

