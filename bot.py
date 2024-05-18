import os
import re
import requests
import asyncio
from telegram import Update, InputFile
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
    IMGUR_CLIENT_ID = get_env_variable('IMGUR_CLIENT_ID')
except EnvironmentError as e:
    print(e)
    exit(1)

FARCASTER_URL = "https://api.neynar.com/v2/farcaster/cast"  # Farcaster API endpoint
IMGUR_UPLOAD_URL = "https://api.imgur.com/3/image"  # Imgur API endpoint
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
    "degen": "degen",
    "travel": "travel",
    "ai": "ai",
    "crypto": "crypto"
    # Add more channels here as needed
}

# Regular expression to find URLs
URL_REGEX = r'(https?://[^\s]+)'

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.channel_post
    if message:
        print("Message in channel noticed!")
        if message.text or message.caption:
            text_content = message.text or message.caption
            print(f"New message in the channel: {text_content}")
            # Process the text and/or photo message (send to Farcaster)
            await process_message_and_photo(message, text_content)
        elif message.photo:
            print("New photo in the channel.")
            # Process the photo message (upload to Imgur and send to Farcaster)
            await process_photo(message)

async def process_message_and_photo(message, text_content: str) -> None:
    # Determine the Farcaster channel based on the prefix in the message
    channel_id = DEFAULT_CHANNEL_ID
    if text_content.startswith('/'):
        split_message = text_content.split(' ', 1)
        prefix = split_message[0][1:]
        if prefix in CHANNEL_MAP:
            channel_id = CHANNEL_MAP[prefix]
            text_content = split_message[1] if len(split_message) > 1 else ""
        else:
            print(f"Unknown channel prefix: {prefix}. Defaulting to {DEFAULT_CHANNEL_ID}.")

    # Check message length
    if len(text_content) > MAX_CAST_LENGTH:
        print(f"Error: Message exceeds {MAX_CAST_LENGTH} characters and will not be sent to Farcaster.")
        return

    # Find URLs in the text content
    urls = re.findall(URL_REGEX, text_content)
    if urls:
        embeds = [{"url": url} for url in urls]
        # Remove URLs from the text content
        for url in urls:
            text_content = text_content.replace(url, "").strip()
    else:
        embeds = []

    if message.photo:
        # Process the photo message (upload to Imgur and send to Farcaster)
        photo = message.photo[-1]  # Get the highest resolution photo
        file = await photo.get_file()
        file_path = file.file_path

        # Download the image locally
        local_file_path = await download_image(file_path)

        # Upload the image to Imgur
        image_url = await upload_image_to_imgur(local_file_path)

        if image_url:
            embeds.append({"url": image_url})

        # Delete the local file after processing
        await delete_local_file(local_file_path)

    print(f"Posting to channel: {channel_id}")
    await send_to_farcaster(text_content, channel_id, embeds)

async def process_photo(message) -> None:
    photo = message.photo[-1]  # Get the highest resolution photo
    file = await photo.get_file()
    file_path = file.file_path

    # Download the image locally
    local_file_path = await download_image(file_path)

    # Upload the image to Imgur
    image_url = await upload_image_to_imgur(local_file_path)

    if image_url:
        # Prepare the Farcaster cast with the image URL embedded
        await send_to_farcaster("", DEFAULT_CHANNEL_ID, [{"url": image_url}])

    # Delete the local file after processing
    await delete_local_file(local_file_path)

async def download_image(file_url: str) -> str:
    local_filename = file_url.split('/')[-1]
    local_file_path = os.path.join(os.getcwd(), local_filename)
    response = await asyncio.to_thread(requests.get, file_url)
    
    if response.status_code == 200:
        with open(local_file_path, 'wb') as file:
            file.write(response.content)
        print(f"Image downloaded successfully: {local_file_path}")
        return local_file_path
    else:
        print(f"Failed to download image: {response.text}")
        return None

async def upload_image_to_imgur(file_path: str) -> str:
    headers = {
        "Authorization": f"Client-ID {IMGUR_CLIENT_ID}"
    }
    with open(file_path, 'rb') as image_file:
        response = await asyncio.to_thread(requests.post, IMGUR_UPLOAD_URL, headers=headers, files={'image': image_file})
    
    if response.status_code == 200:
        image_url = response.json()['data']['link']
        print(f"Image uploaded successfully: {image_url}")
        return image_url
    else:
        print(f"Failed to upload image: {response.text}")
        return None

async def delete_local_file(file_path: str) -> None:
    try:
        os.remove(file_path)
        print(f"Local file deleted: {file_path}")
    except Exception as e:
        print(f"Error deleting local file: {e}")

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
