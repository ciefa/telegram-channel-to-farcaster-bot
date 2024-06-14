# Telegram Channel To Farcaster Bot

This project monitors a specified Telegram channel and posts messages from that channel to the Farcaster social network.

Important note:

I am truly bad/new at programming and barely know anything, I've used ChatGPT 4o to help me create this script.

This is probably not the best/most efficient way to do it, but it works for me so.. `¯\_(ツ)_/¯`

To get an idea what this does, feel free to check out my Telegram channel and my Farcaster channel:

[Telegram](https://t.me/ciefascorner)

[Farcaster](https://warpcast.com/~/channel/ciefascorner)

As you can see, whatever I post in my TG channel will be relayed to my Farcaster channel.

## Usage

You write a message in your Telegram channel and it will automatically be casted on Farcaster.
If you do not specify a channel, it'll default to the default channel specified in the .env.
Right now it's set to /replyguys.

If you want to have your Telegram channel message casted into a specific channel, type the channel name with a / in front of it first.

For example, if you want to cast "Hello World" into the /farcaster channel, you'd write the following in your Telegram channel:

```/farcaster Hello World```

Of course the /farcaster will be ignored for the actual cast! The actual would be just "Hello World" inside /farcaster.

You can also post images into the Telegram channel and they will be casted as well.

You can also delete a cast through a message in the channel:

```
    /delete <cast_hash>
```
Once a cast is submitted, both the console as well as the channel will receive the cast hash.

## Images

**IMPORTANT: To make use of this feature, you need to register for a (free) Imgur client ID. Add said ID to the .env**

**Note that you HAVE TO compress the image when posting, simply click the check box "compress image" when pasting an image into your TG channel.**

If you paste an image into your channel, the bot will download said image locally to then upload it to Imgur.
The image url is then added to the embed part of the payload.

## Requirements

- Python 3.x
- python-dotenv
- python-telegram-bot
- requests

## Setup
  
1. **Clone the repository**:

```
   git clone https://github.com/ciefa/telegram-channel-to-farcaster-bot.git

   cd telegram-channel-to-farcaster-bot
```

2. **Create a virtual environment and activate it (optional but recommended):**

```
    python -m venv venv

    source venv/bin/activate   # On Windows: venv\Scripts\activate
```

3.  **Install the required dependencies:**

```
    pip install -r requirements.txt
```

4. **Create a .env file:**

```
    cp .env.template .env

    Fill in the .env file with your own credentials.
```

5. **Run the bot:**

```
    python bot.py
    python server.py
```

## Important Information

Make sure that your Telegram bot is inside the Telegram channel from where you want to cast from.

The bot is now using a Flask server, so you can deploy this project easily on something like Replit.

If you do so, make sure to NOT use .env and instead use the Secrets system that Replit has in place!

The Telegram bot also needs admin perms!

You will need the channel_id of your Telegram channel, too.
I got mine by forwarding a message from my channel to the @JsonDumpBot bot.

## Adding more channels

To add more channels, head into the bot.py code and add channels to CHANNEL_MAP.

## Support

If you have problems or questions, please feel free to hit me up on Farcaster!

[farcaster.id](https://www.farcaster.id/ciefa.eth)

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License

[MIT](https://github.com/ciefa/telegram-channel-to-farcaster-bot/blob/main/LICENSE)
