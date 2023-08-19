import os
import re
import openai
import argparse
import feedparser
from telethon import TelegramClient

TELEGRAM_CHANNEL_ID = int(os.getenv('TELEGRAM_CHANNEL_ID'))
TELEGRAM_APP_ID = os.getenv('TELEGRAM_API_ID')
TELEGRAM_API_HASH = os.getenv('TELEGRAM_API_HASH')
BLOG_RSS_FEED_URL = os.getenv('BLOG_RSS_FEED_URL')
openai.api_key = os.getenv('OPENAI_API_KEY')

async def generate_summary(text):
    prompt = (f"Write a short three sentence summary to the following blog post from the first person:\n###{text}###\n Reply with a summary only. Start with 'In this post, I wrote about ...")
    response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", 
                       "content": prompt}],
        )
    summary = response.choices[0].message.content
    return summary

async def main(no_summary):
    # Get the existing links from the channel
    urls = []
    async for message in client.iter_messages(TELEGRAM_CHANNEL_ID):
        urls += re.findall("(?P<url>https?://[^\s]+)", str(message.text))
    feed = feedparser.parse(BLOG_RSS_FEED_URL)
    entries = sorted(feed.entries, key=lambda entry: entry.published_parsed)
    for entry in entries:
        link = entry.link
        if link not in urls: # Only post if the link hasn't been posted before
            if no_summary:
                message = f'"{entry.title}"\n---\n{link}'
            else:
                try: # sometimes the post is too long and OpenAI API fails because of the context length limit
                    summary = await generate_summary(entry.summary)
                    message = f'"{entry.title}"\n---\n{summary}\n---\n{link}'
                except Exception as e:
                    print(e)
            await client.send_message(TELEGRAM_CHANNEL_ID, message)
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--no-summary', '-ns', action='store_true', help='Disable post summary generation')
    args = parser.parse_args()
    client = TelegramClient('my-client', TELEGRAM_APP_ID, TELEGRAM_API_HASH).start(phone="1-438-350-9706")
    with client:
        client.loop.run_until_complete(main(args.no_summary))