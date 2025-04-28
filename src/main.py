from bot import DiscordBot
from settings import BOT_TOKEN, GUILD_ID, CHANNEL_ID

if __name__ == '__main__':
    bot = DiscordBot(BOT_TOKEN, GUILD_ID, CHANNEL_ID)
    bot.run()