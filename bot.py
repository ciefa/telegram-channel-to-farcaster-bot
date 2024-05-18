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
    "crypto": "crypto",
    "alfafrens": "alfafrens",
    "base": "base",
    "adhd": "adhd",
    "nova": "nova",
    "cypher": "cypher",
    "ens": "ens",
    "ethrd": "ethrd",
    "evm": "evm",
    "europe": "europe",
    "finance": "finance",
    "fitness": "fitness",
    "frames": "frames",
    "founders": "founders",
    "allotment": "allotment",
    "gardening": "gardening"
    # Add more channels here as needed
}

# Regular expression to find URLs
URL_REGEX = r'(https?://[^\s]+)'

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.channel_post:
        message = update.channel_post
        text_content = message.text or message.caption or ""

        print("\n" + "=" * 40)
        print(f"Message in channel noticed!\nNew message in the channel: {text_content}")
        print("=" * 40)

        # Check if the message is a delete command
        if text_content.lower().startswith("/delete"):
            command_parts = text_content.split(' ')
            if len(command_parts) == 2:
                cast_hash = command_parts[1]
                print(f"Delete command received. Cast hash: {cast_hash}")
                await delete_cast(cast_hash, context, message.chat_id)
            else:
                print("Invalid /delete command format. Usage: /delete <cast_hash>")
            print("=" * 40)
            return

        # Process the text and/or photo message (send to Farcaster)
        if message.text or message.caption:
            await process_message_and_photo(message, text_content, context)
        elif message.photo:
            await process_photo(message, context)

async def process_message_and_photo(message, text_content: str, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Determine the Farcaster channel based on the prefix in the message
    channel_id = DEFAULT_CHANNEL_ID
    if text_content.startswith('/'):
        split_message = text_content.split(' ', 1)
        prefix = split_message[0][1:]
        if prefix in CHANNEL_MAP:
            channel_id = CHANNEL_MAP[prefix]
            text_content = split_message[1] if len(split_message) > 1 else ""

    # Check message length
    if len(text_content) > MAX_CAST_LENGTH:
        print(f"Error: Message exceeds {MAX_CAST_LENGTH} characters and will not be sent to Farcaster.")
        print("=" * 40)
        return

    # Find URLs in the text content
    urls = re.findall(URL_REGEX, text_content)
    embeds = []

    # Remove URLs from the text content
    for url in urls:
        text_content = text_content.replace(url, "").strip()

    image_url = None

    if message.photo:
        # Process the photo message (upload to Imgur and send to Farcaster)
        photo = message.photo[-1]  # Get the highest resolution photo
        file = await photo.get_file()
        file_path = file.file_path

        print(f"Downloading image locally: {file_path}")
        # Download the image locally
        local_file_path = await download_image(file_path)

        print(f"Uploading image to Imgur: {local_file_path}")
        # Upload the image to Imgur
        image_url = await upload_image_to_imgur(local_file_path)

        # Delete the local file after processing
        print(f"Deleting local file: {local_file_path}")
        await delete_local_file(local_file_path)

    if image_url:
        print(f"Image uploaded successfully to Imgur. URL: {image_url}")
        print("=" * 40)
        # Include the image URL as a priority
        embeds.append({"url": image_url})

    # Include up to two URLs from the text, ensuring the total number of embeds does not exceed 2
    for url in urls:
        if len(embeds) < 2:
            embeds.append({"url": url})
        else:
            print(f"Skipping URL due to embed limit: {url}")

    if len(embeds) > 2:
        print(f"Image and URL posted, but {len(embeds) - 2} URL(s) had to be skipped due to the limit of 2 embeds in the API.")

    cast_hash = await send_to_farcaster(text_content, channel_id, embeds)

    # Send a message with the cast hash for easy deletion reference
    if cast_hash:
        print(f"Cast published successfully. Cast hash: {cast_hash}")
        print("=" * 40)
        await context.bot.send_message(
            chat_id=message.chat_id,
            text=f"Cast hash: {cast_hash}"
        )

async def process_photo(message, context: ContextTypes.DEFAULT_TYPE) -> None:
    photo = message.photo[-1]  # Get the highest resolution photo
    file = await photo.get_file()
    file_path = file.file_path

    print(f"Downloading image locally: {file_path}")
    # Download the image locally
    local_file_path = await download_image(file_path)

    print(f"Uploading image to Imgur: {local_file_path}")
    # Upload the image to Imgur
    image_url = await upload_image_to_imgur(local_file_path)

    if image_url:
        print(f"Image uploaded successfully to Imgur. URL: {image_url}")
        # Prepare the Farcaster cast with the image URL embedded
        cast_hash = await send_to_farcaster("", DEFAULT_CHANNEL_ID, [{"url": image_url}])

        # Send a message with the cast hash for easy deletion reference
        if cast_hash:
            print(f"Cast published successfully. Cast hash: {cast_hash}")
            print("=" * 40)
            await context.bot.send_message(
                chat_id=message.chat_id,
                text=f"/info Cast hash: {cast_hash}"
            )

    # Delete the local file after processing
    print(f"Deleting local file: {local_file_path}")
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

async def send_to_farcaster(message_text: str, channel_id: str, embeds: list) -> str:
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
            response_data = response.json()
            cast_hash = response_data.get("cast", {}).get("hash")
            if cast_hash:
                return cast_hash
        else:
            print(f"Failed to publish cast: {response.text}")
    except Exception as e:
        print(f"Error while sending to Farcaster: {e}")
    return None

async def delete_cast(cast_hash: str, context: ContextTypes.DEFAULT_TYPE, chat_id: int) -> None:
    # Delete the cast from Farcaster using the Farcaster API
    payload = {
        "signer_uuid": SIGNER_UUID,
        "target_hash": cast_hash
    }
    headers = {
        "accept": "application/json",
        "api_key": FARCASTER_API_KEY,
        "content-type": "application/json"
    }
    try:
        response = await asyncio.to_thread(requests.delete, FARCASTER_URL, json=payload, headers=headers)
        if response.status_code == 200:
            print(f"Cast deleted successfully. Cast hash: {cast_hash}")
            print("=" * 40)
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"Cast deleted successfully. Cast hash: {cast_hash}"
            )
        else:
            print(f"Failed to delete cast: {response.text}")
    except Exception as e:
        print(f"Error while deleting cast: {e}")

def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Add handler to process channel posts and messages
    application.add_handler(MessageHandler(filters.ALL, message_handler))

    # Print a message indicating the bot is waiting for input
    print("Waiting for input in channel")
    print("=" * 40)

    # Start the Bot
    application.run_polling()

if __name__ == '__main__':
    main()
