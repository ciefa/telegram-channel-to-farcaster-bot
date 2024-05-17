import os
import re
import requests
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Function to get environment variables with error handling
def get_env_variable(var_name):
    value = os.getenv(var_name)
    if value is None:
        raise EnvironmentError(f"Required environment variable '{var_name}' not found.")
    return value

try:
    # Get environment variables
    BOT_TOKEN = get_env_variable('BOT_TOKEN')
    FARCASTER_API_KEY = get_env_variable('FARCASTER_API_KEY')
    SIGNER_UUID = get_env_variable('SIGNER_UUID')
    DEFAULT_CHANNEL_ID = get_env_variable('DEFAULT_CHANNEL_ID')
except EnvironmentError as e:
    print(e)
    exit(1)

FARCASTER_URL = "https://api.neynar.com/v2/farcaster/cast"  # Farcaster API endpoint
MAX_CAST_LENGTH = 320  # Maximum allowed character length for a Farcaster cast

# Mapping of Telegram command prefixes to Farcaster channel IDs
# Since we are using Neynar API, we can specify channel just by what they're called on Farcaster.
# For example, the channel /history would be "history": "history"
CHANNEL_MAP = {
    "gaming": "gaming",
    "sonata": "sonata",
    "replyguys": "replyguys",
    "history": "history",
    "farcaster": "farcaster",
    "dev": "dev",
    "ethereum": "ethereum",
    "base": "base",
    "degen": "degen"
    # Add more channels here as needed
}

# Regular expression to find URLs
URL_REGEX = r'(https?://[^\s]+)'

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.channel_post
    if message:
        print("Message in channel noticed!")
        print(f"New message in the channel: {message.text}")

        # Process the message (send to Farcaster)
        await process_message(message.text)

async def process_message(message_text: str) -> None:
    # Determine the Farcaster channel based on the prefix in the message
    channel_id = DEFAULT_CHANNEL_ID
    if message_text.startswith('/'):
        split_message = message_text.split(' ', 1)
        prefix = split_message[0][1:]
        if prefix in CHANNEL_MAP:
            channel_id = CHANNEL_MAP[prefix]
            message_text = split_message[1] if len(split_message) > 1 else ""
        else:
            print(f"Unknown channel prefix: {prefix}. Defaulting to {DEFAULT_CHANNEL_ID}.")

    # Check message length
    if len(message_text) > MAX_CAST_LENGTH:
        print(f"Error: Message exceeds {MAX_CAST_LENGTH} characters and will not be sent to Farcaster.")
        return

    # Find URLs in the message text
    urls = re.findall(URL_REGEX, message_text)
    if urls:
        embeds = [{"url": url} for url in urls]
        # Remove URLs from the message text
        for url in urls:
            message_text = message_text.replace(url, "").strip()
    else:
        embeds = []

    print(f"Posting to channel: {channel_id}")
    await send_to_farcaster(message_text, channel_id, embeds)

async def send_to_farcaster(message_text: str, channel_id: str, embeds: list) -> None:
    # Send the message to Farcaster using the Farcaster API
    payload = {
        "text": message_text,
        "channel_id": channel_id,
        "signer_uuid": SIGNER_UUID
    }
    if embeds:
        payload["embeds"] = embeds
    headers = {
        "accept": "application/json",
        "api_key": FARCASTER_API_KEY,
        "content-type": "application/json"
    }
    try:
        response = await asyncio.to_thread(requests.post, FARCASTER_URL, json=payload, headers=headers)
        if response.status_code == 200:
            print("Cast published successfully")
        else:
            print(f"Failed to publish cast: {response.text}")
    except Exception as e:
        print(f"Error while sending to Farcaster: {e}")

def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Add handler to process channel posts
    application.add_handler(MessageHandler(filters.UpdateType.CHANNEL_POST, message_handler))

    # Print a message indicating the bot is waiting for input
    print("Waiting for input in channel")

    # Start the Bot
    application.run_polling()

if __name__ == '__main__':
    main()
