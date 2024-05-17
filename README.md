# Telegram to Farcaster Bot

This project monitors a specified Telegram channel and posts messages from that channel to the Farcaster social network.

Important note:

I am truly bad at programming and barely know anything, I've used ChatGPT 4o to help me create this script.

To get an idea what this does, feel free to check out my Telegram channel and my Farcaster channel:

[Telegram](https://t.me/ciefascorner)

[Farcaster](https://warpcast.com/~/channel/ciefascorner)

As you can see, whatever I post in my TG channel will be relayed to my Farcaster channel.

## Requirements

- Python 3.x
- python-dotenv
- python-telegram-bot
- requests
## Setup
  
1. **Clone the repository**:

```sh

   git clone https://github.com/yourusername/your-repo-name.git

   cd your-repo-name
```

2. **Create a virtual environment and activate it (optional but recommended):**

```python -m venv venv

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
```

## Important Information

Make sure that your Telegram bot is inside the Telegram channel from where you want to cast from.

The Telegram bot also needs admin perms!

You will need the channel_id of your Telegram channel, too.
I got mine by forwarding a message from my channel to the @JsonDumpBot bot.

## Channels and adding more channels

You can cast into a channel if you type "/" followed by a channel name AFTER you have added the channel to the channel_mapping.

For example, if you want to cast "Hello World" into the /gaming channel, you type the following into your Telegram channel:

/gaming Hello World

To add more channels, head into the script.py code and add channels to the channel_mapping.
## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.
## License

[MIT](https://github.com/ciefa/telegram-channel-to-farcaster-bot/blob/main/LICENSE)