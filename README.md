# Telegram Bot | Stream Recorder and Manager

This script is designed to manage and record live streams from various platforms such as Twitch, YouTube, and Q-dance. It integrates with Telegram to allow remote control and monitoring of the recording processes.

## Features

- **Start and Stop Recordings**: Begin or halt recording of streams from Twitch, YouTube, and Q-dance.
- **Add and Delete Streams**: Manage the list of streams to record by adding new ones or removing existing entries.
- **List Streams**: Display the current list of configured streams for each platform.
- **Status Updates**: Check the status of ongoing recordings, including elapsed time and recording type.
- **Telegram Bot Integration**: Interact with the script via a Telegram bot, which provides a user-friendly interface for managing recordings.
- **Donation Support**: Includes an option for users to support the project through donations.

## Configuration

The script requires a `config.json` file for setup. This file should contain:
- `telegram_bot_token`: The token for your Telegram bot.
- `telegram_chat_id`: The chat ID for Telegram bot interactions.
- `recording_path`: The directory where recordings will be saved.
- `qdance_credentials`: Your Q-dance login credentials (username and password).

## How to Use

1. **Start Recording**: Use the `/record` command to begin recording all streams listed in the configuration.
2. **Stop Recording**: Use the `/save` command to stop all active recordings.
3. **Add a Stream**: Use the `/add` command and follow the prompts to add Twitch, YouTube, or Q-dance streams.
4. **Delete a Stream**: Use the `/remove` command to delete a specific stream.
5. **List Streams**: Use the `/list` command to view all configured streams.
6. **Check Status**: Use the `/status` command to get the status of ongoing recordings.
7. **Help**: Use the `/help` command to get a list of available commands and their usage.

## Dependencies

- `telebot`: For Telegram bot interaction.
- `websockets`: For handling WebSocket connections (if needed).
- `json`, `os`, `re`, `subprocess`, `time`, `threading`, `hashlib`: Standard Python libraries used in the script.
- `streamlink`: For recording Twitch streams. (You need the [streamlink-ttvlol](https://github.com/2bc4/streamlink-ttvlol/) plugin, i'm using a AdBlock Proxy!)
- `yt-dlp`: For recording YouTube and Q-dance streams.

## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/revunix/StreamREC-TelegramBot.git
    ```

2. Install required Python packages:
    ```bash
    pip install pyTelegramBotAPI streamlink yt-dlp
    ```

3. Update the `config.json` file with your credentials and paths.

4. Run the script:
    ```bash
    python streamrec.py
    ```

## Contributing

Feel free to contribute by submitting issues or pull requests. For any questions or support, open an issue on GitHub.

---

Let me know if you need any adjustments or additional details!
