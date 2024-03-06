import os
import discord
import csv
from discord.ext import commands
from textblob import TextBlob

TOKEN = ''  # your token here

IGNORED_USERS = [  # add users to ignore here (like other bots)
    "Deleted User"
]

intents = discord.Intents.default()
intents.messages = True

bot = commands.Bot(command_prefix='!', intents=intents)


def replace_mentions(content, message):
    for mention in message.mentions:
        content = content.replace(f"<@{mention.id}>", f"@{mention.name}")
    return content


def get_sentiment(text):
    analysis = TextBlob(text)
    return analysis.sentiment.polarity


async def scrape_messages(guild):
    folder_name = f"{guild.name}_data"
    os.makedirs(folder_name, exist_ok=True)
    filename = os.path.join(folder_name, f"{guild.name}_messages.csv")
    avg_sentiment_filename = os.path.join(folder_name, f"{guild.name}_average_sentiment.csv")
    users = {}
    with open(filename, 'w', newline='', encoding='utf-8') as file, \
            open(avg_sentiment_filename, 'w', newline='', encoding='utf-8') as avg_sentiment_file:
        writer = csv.writer(file)
        avg_sentiment_writer = csv.writer(avg_sentiment_file)
        writer.writerow(["Author", "Message", "Sentiment"])
        avg_sentiment_writer.writerow(["User", "Average Sentiment"])
        for channel in guild.text_channels:
            async for message in channel.history(limit=None):
                if message.content and message.author.name not in IGNORED_USERS:
                    content = replace_mentions(message.content, message)
                    sentiment_score = get_sentiment(content)
                    writer.writerow([message.author.name, content, sentiment_score])
                    if message.author.name not in users:
                        users[message.author.name] = [sentiment_score, 1]
                    else:
                        users[message.author.name][0] += sentiment_score
                        users[message.author.name][1] += 1
        for user, (total_sentiment, message_count) in users.items():
            avg_sentiment = total_sentiment / message_count
            avg_sentiment_writer.writerow([user, avg_sentiment])

            avg_sentiment_file.seek(0)
            next(avg_sentiment_file)
            sorted_data = sorted(csv.reader(avg_sentiment_file), key=lambda x: float(x[1]))
            avg_sentiment_file.seek(0)
            avg_sentiment_writer = csv.writer(avg_sentiment_file)
            avg_sentiment_writer.writerow(["User", "Average Sentiment"])
            avg_sentiment_writer.writerows(sorted_data)


@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

    for guild in bot.guilds:
        print(f'Connected to guild: {guild.name}')
        await scrape_messages(guild)


bot.run(TOKEN)
