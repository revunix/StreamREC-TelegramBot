import json
import websockets
import os
import re
import subprocess
import telebot
import time
import threading
import hashlib
from threading import Thread
from datetime import datetime

# Lade Konfiguration
def load_config():
    with open('config.json', 'r') as f:
        return json.load(f)

def save_config(config):
    with open('config.json', 'w') as f:
        json.dump(config, f, indent=4)

config = load_config()

TELEGRAM_BOT_TOKEN = config['telegram_bot_token']
TELEGRAM_CHAT_ID = config['telegram_chat_id']
RECORDING_PATH = config['recording_path']
TWITCH_PROXY = "https://as.luminous.dev"
QDANCE_USERNAME = config['qdance_credentials']['username']
QDANCE_PASSWORD = config['qdance_credentials']['password']

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# Regex-Muster für URL-Erkennung
TWITCH_REGEX = re.compile(r'(https?://)?(www\.)?(twitch\.tv/)')
YOUTUBE_REGEX = re.compile(r'(https?://)?(www\.)?(youtube\.com/watch\?v=)')
QDANCE_REGEX = re.compile(r'(https?://)?(www\.)?(q-dance\.com/network)')

# Speichert die aktuellen Aufnahme-Threads
active_recordings = {}

def show_main_menu(chat_id):
    markup = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    item1 = telebot.types.KeyboardButton('Start Recording')
    item2 = telebot.types.KeyboardButton('Add Stream')
    item3 = telebot.types.KeyboardButton('Delete Stream')
    item4 = telebot.types.KeyboardButton('List Streams')
    item5 = telebot.types.KeyboardButton('Status')
    item6 = telebot.types.KeyboardButton('Donate')  # Add a Donate button
    markup.add(item1, item2, item3, item4, item5, item6)
    bot.send_message(chat_id, "Select an option:", reply_markup=markup)

def show_stop_menu(chat_id):
    markup = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    item1 = telebot.types.KeyboardButton('Stop Recording')
    item2 = telebot.types.KeyboardButton('Status')
    markup.add(item1, item2)
    bot.send_message(chat_id, "Select an option:", reply_markup=markup)

def record_twitch_stream(url, path, start_time):
    while True:
        # Überprüfen, ob der Stream bereits aktiv ist
        if url in active_recordings:
            print(f"Stream for URL `{url}` is already active.")
            return
        
        command = ['streamlink', url, 'best', '--twitch-proxy-playlist={}'.format(TWITCH_PROXY), '--retry-streams', '30', '-o', path]
        process = subprocess.Popen(command)
        
        # Registriere den Prozess als aktiv
        active_recordings[url] = {
            'process': process,
            'start_time': start_time,
            'type': 'Twitch'
        }
        
        try:
            while True:
                if process.poll() is not None:
                    # Der Stream wurde nicht mehr aufgenommen
                    if process.returncode == 0:
                        # Erfolgreich aufgenommen
                        break
                    else:
                        # Fehler beim Aufnehmen des Streams
                        print(f"Recording failed for URL `{url}`. Retrying in 30 seconds...")
                        active_recordings.pop(url, None)
                        time.sleep(30)  # Warte 30 Sekunden bevor der Stream neu gestartet wird
                        break
                
                # Überprüfe, ob der Stream gestoppt werden soll
                if url not in active_recordings:
                    process.terminate()
                    print(f"Recording stopped for URL `{url}`.")
                    return
        except KeyboardInterrupt:
            print(f"Recording interrupted for URL `{url}`.")
            process.terminate()
            active_recordings.pop(url, None)
            return

def record_youtube_stream(url, path, start_time):
    while True:
        # Überprüfen, ob der Stream bereits aktiv ist
        if url in active_recordings:
            print(f"Stream for URL `{url}` is already active.")
            return
        
        command = ['yt-dlp', url, '-o', path]
        process = subprocess.Popen(command)
        
        # Registriere den Prozess als aktiv
        active_recordings[url] = {
            'process': process,
            'start_time': start_time,
            'type': 'YouTube'
        }
        
        try:
            while True:
                if process.poll() is not None:
                    # Der Stream wurde nicht mehr aufgenommen
                    if process.returncode == 0:
                        # Erfolgreich aufgenommen
                        break
                    else:
                        # Fehler beim Aufnehmen des Streams
                        print(f"Recording failed for URL `{url}`. Retrying in 30 seconds...")
                        active_recordings.pop(url, None)
                        time.sleep(30)  # Warte 30 Sekunden bevor der Stream neu gestartet wird
                        break
                
                # Überprüfe, ob der Stream gestoppt werden soll
                if url not in active_recordings:
                    process.terminate()
                    print(f"Recording stopped for URL `{url}`.")
                    return
        except KeyboardInterrupt:
            print(f"Recording interrupted for URL `{url}`.")
            process.terminate()
            active_recordings.pop(url, None)
            return

def record_qdance_stream(url, path, username, password, start_time):
    command = ['yt-dlp', url, '--username', username, '--password', password, '-o', path]
    process = subprocess.Popen(command)
    active_recordings[url] = {
        'process': process,
        'start_time': start_time,
        'type': 'Q-dance'
    }
    process.wait()
    active_recordings.pop(url, None)

def start_twitch_recordings():
    for stream in config['twitch_streams']:
        url = stream['url']
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        path = os.path.join(RECORDING_PATH, 'twitch_{}_{}.mp4'.format(url.split('/')[-1], timestamp))
        Thread(target=record_twitch_stream, args=(url, path, datetime.now())).start()

def start_youtube_recordings():
    for stream in config['youtube_streams']:
        url = stream['url']
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        path = os.path.join(RECORDING_PATH, 'youtube_{}_{}.mp4'.format(url.split('=')[-1], timestamp))
        Thread(target=record_youtube_stream, args=(url, path, datetime.now())).start()

def start_qdance_recordings():
    for stream in config['qdance_streams']:
        url = stream['url']
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        path = os.path.join(RECORDING_PATH, 'qdance_{}_{}.mp4'.format(url.split('/')[-1], timestamp))
        Thread(target=record_qdance_stream, args=(url, path, QDANCE_USERNAME, QDANCE_PASSWORD, datetime.now())).start()

@bot.message_handler(commands=['rec_start'])
def rec_start(message):
    if str(message.chat.id) == TELEGRAM_CHAT_ID:
        # Starte die Aufnahme-Threads für alle Streams
        start_twitch_recordings()
        start_youtube_recordings()
        start_qdance_recordings()
        
        # Zeige den Status der aktuellen Aufnahmen an
        if not active_recordings:
            status_message = "No streams are currently recording."
        else:
            status_message = "Current streams being recorded:\n"
            for url, info in active_recordings.items():
                elapsed_time = datetime.now() - info['start_time']
                status_message += "`{}` (Type: {})\nStarted: {}\nElapsed Time: {}\n\n".format(
                    url, info['type'], info['start_time'].strftime('%Y-%m-%d %H:%M:%S'), str(elapsed_time).split('.')[0])
        
        # Zeige den Status an
        bot.send_message(message.chat.id, status_message, parse_mode='Markdown')
        
        # Zeige das Menü an
        markup = telebot.types.ReplyKeyboardMarkup(row_width=2)
        item1 = telebot.types.KeyboardButton('Stop Streams')
        item2 = telebot.types.KeyboardButton('Status')
        markup.add(item1, item2)
        bot.send_message(message.chat.id, "Select an option:", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "Unauthorized access.")

@bot.message_handler(func=lambda message: message.text in ['Stop Streams', 'Status'])
def handle_rec_start_options(message):
    if str(message.chat.id) == TELEGRAM_CHAT_ID:
        if message.text == 'Stop Streams':
            markup = telebot.types.ReplyKeyboardMarkup(row_width=1)
            item1 = telebot.types.KeyboardButton('Confirm Stop')
            item2 = telebot.types.KeyboardButton('Cancel')
            markup.add(item1, item2)
            bot.send_message(message.chat.id, "Are you sure you want to stop all streams?", reply_markup=markup)
            bot.register_next_step_handler(message, confirm_stop_streams)
        elif message.text == 'Status':
            status(message)
    else:
        bot.send_message(message.chat.id, "Unauthorized access.")

def confirm_stop_streams(message):
    if str(message.chat.id) == TELEGRAM_CHAT_ID:
        if message.text == 'Confirm Stop':
            for recording in active_recordings.values():
                recording['process'].terminate()
            active_recordings.clear()
            bot.send_message(message.chat.id, "Recording stopped for all streams.")
            
            # Entfernt das Tastatur-Menü
            bot.send_message(message.chat.id, "Streams have been stopped.")
            
            # Neues Menü anzeigen
            markup = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
            item1 = telebot.types.KeyboardButton('Start Recording')
            item2 = telebot.types.KeyboardButton('Add Stream')
            item3 = telebot.types.KeyboardButton('Delete Stream')
            item4 = telebot.types.KeyboardButton('List Streams')
            markup.add(item1, item2, item3, item4)
            bot.send_message(message.chat.id, "Select an option:", reply_markup=markup)
        elif message.text == 'Cancel':
            bot.send_message(message.chat.id, "Stopping streams has been cancelled.")
            
            # Zeigt das ursprüngliche Menü erneut an
            markup = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
            item1 = telebot.types.KeyboardButton('Stop Streams')
            item2 = telebot.types.KeyboardButton('Status')
            markup.add(item1, item2)
            bot.send_message(message.chat.id, "Select an option:", reply_markup=markup)
        else:
            bot.send_message(message.chat.id, "Invalid option. Use /rec_start to start over.")
    else:
        bot.send_message(message.chat.id, "Unauthorized access.")

@bot.message_handler(commands=['rec_stop'])
def rec_stop(message):
    if str(message.chat.id) == TELEGRAM_CHAT_ID:
        for recording in active_recordings.values():
            recording['process'].terminate()
        active_recordings.clear()
        bot.send_message(TELEGRAM_CHAT_ID, "Recording stopped for all streams.")
    else:
        bot.send_message(message.chat.id, "Unauthorized access.")

@bot.message_handler(commands=['add'])
def add(message):
    if str(message.chat.id) == TELEGRAM_CHAT_ID:
        markup = telebot.types.ReplyKeyboardMarkup(row_width=1)
        item1 = telebot.types.KeyboardButton('Add Twitch Stream')
        item2 = telebot.types.KeyboardButton('Add YouTube Stream')
        item3 = telebot.types.KeyboardButton('Add Q-dance Stream')
        markup.add(item1, item2, item3)
        bot.send_message(message.chat.id, "Select the type of stream to add:", reply_markup=markup)
        bot.register_next_step_handler(message, process_add_selection)
    else:
        bot.send_message(message.chat.id, "Unauthorized access.")

def process_add_selection(message):
    stream_type = message.text
    if stream_type == 'Add Twitch Stream':
        bot.send_message(message.chat.id, "Please send the Twitch username.")
        bot.register_next_step_handler(message, add_twitch_stream)
    elif stream_type == 'Add YouTube Stream':
        bot.send_message(message.chat.id, "Please send the YouTube video ID.")
        bot.register_next_step_handler(message, add_youtube_stream)
    elif stream_type == 'Add Q-dance Stream':
        bot.send_message(message.chat.id, "Please send the Q-dance stream URL.")
        bot.register_next_step_handler(message, add_qdance_stream)
    else:
        bot.send_message(message.chat.id, "Invalid selection. Use /add to start over.")
        show_main_menu(message.chat.id)  # Return to the main menu

def add_twitch_stream(message):
    username = message.text
    url = f"https://twitch.tv/{username}"
    if TWITCH_REGEX.match(url):
        if any(stream['url'] == url for stream in config['twitch_streams']):
            bot.send_message(TELEGRAM_CHAT_ID, "Twitch stream URL `{}` is already added.".format(url))
        else:
            config['twitch_streams'].append({"url": url})
            save_config(config)
            bot.send_message(TELEGRAM_CHAT_ID, "Twitch stream added: `{}`".format(url))
    else:
        bot.send_message(TELEGRAM_CHAT_ID, "Invalid Twitch URL. Please try again.")
    show_main_menu(message.chat.id)  # Return to the main menu

def add_youtube_stream(message):
    video_id = message.text
    url = f"https://youtube.com/watch?v={video_id}"
    if YOUTUBE_REGEX.match(url):
        if any(stream['url'] == video_id for stream in config['youtube_streams']):
            bot.send_message(TELEGRAM_CHAT_ID, "YouTube video ID `{}` is already added.".format(video_id))
        else:
            config['youtube_streams'].append({"url": video_id})
            save_config(config)
            bot.send_message(TELEGRAM_CHAT_ID, "YouTube stream added: `{}`".format(video_id))
    else:
        bot.send_message(TELEGRAM_CHAT_ID, "Invalid YouTube video ID. Please try again.")
    show_main_menu(message.chat.id)  # Return to the main menu

def add_qdance_stream(message):
    url = message.text
    if QDANCE_REGEX.match(url):
        if any(stream['url'] == url for stream in config['qdance_streams']):
            bot.send_message(TELEGRAM_CHAT_ID, "Q-dance stream URL `{}` is already added.".format(url))
        else:
            config['qdance_streams'].append({"url": url})
            save_config(config)
            bot.send_message(TELEGRAM_CHAT_ID, "Q-dance stream added: `{}`".format(url))
    else:
        bot.send_message(TELEGRAM_CHAT_ID, "Invalid Q-dance URL. Please try again.")
    show_main_menu(message.chat.id)  # Return to the main menu

@bot.message_handler(commands=['menu'])
def menu(message):
    if str(message.chat.id) == TELEGRAM_CHAT_ID:
        show_main_menu(message.chat.id)
    else:
        bot.send_message(message.chat.id, "Unauthorized access.")

@bot.message_handler(func=lambda message: message.text in ['Start Recording', 'Add Stream', 'Delete Stream', 'List Streams', 'Stop Recording', 'Status', 'Confirm Stop', 'Cancel', 'Donate'])
def handle_main_menu_options(message):
    if str(message.chat.id) == TELEGRAM_CHAT_ID:
        if message.text == 'Start Recording':
            start_twitch_recordings()
            start_youtube_recordings()
            start_qdance_recordings()
            bot.send_message(message.chat.id, "Recording started for all streams.")
            show_stop_menu(message.chat.id)  # Show the stop menu after starting recordings

        elif message.text == 'Add Stream':
            bot.send_message(message.chat.id, "Please provide the type of stream you want to add:", reply_markup=telebot.types.ReplyKeyboardRemove())
            markup = telebot.types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
            item1 = telebot.types.KeyboardButton('Add Twitch Stream')
            item2 = telebot.types.KeyboardButton('Add YouTube Stream')
            item3 = telebot.types.KeyboardButton('Add Q-dance Stream')
            markup.add(item1, item2, item3)
            bot.send_message(message.chat.id, "Select the type of stream to add:", reply_markup=markup)
            bot.register_next_step_handler(message, process_add_selection)

        elif message.text == 'Delete Stream':
            show_delete_menu(message.chat.id)  # Show the delete menu

        elif message.text == 'List Streams':
            list_streams(message)

        elif message.text == 'Stop Recording':
            markup = telebot.types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
            item1 = telebot.types.KeyboardButton('Confirm Stop')
            item2 = telebot.types.KeyboardButton('Cancel')
            markup.add(item1, item2)
            bot.send_message(message.chat.id, "Are you sure you want to stop recording all streams?", reply_markup=markup)

        elif message.text == 'Status':
            status(message)

        elif message.text == 'Confirm Stop':
            for recording in active_recordings.values():
                recording['process'].terminate()
            active_recordings.clear()
            bot.send_message(message.chat.id, "Recording stopped for all streams.")
            show_main_menu(message.chat.id)  # Show the main menu after stopping recordings

        elif message.text == 'Cancel':
            bot.send_message(message.chat.id, "Recording stop canceled.")
            show_main_menu(message.chat.id)  # Return to the main menu after canceling

        elif message.text == 'Donate':
            markup = telebot.types.InlineKeyboardMarkup()
            donation_button = telebot.types.InlineKeyboardButton(text="Donate", url="https://ko-fi.com/revunix")
            markup.add(donation_button)
            bot.send_message(message.chat.id, "Support the project by donating:", reply_markup=markup)

    else:
        bot.send_message(message.chat.id, "Unauthorized access.")
        
def show_delete_menu(chat_id):
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    
    # Erstelle Inline-Buttons für jede Stream-URL
    for stream in config['twitch_streams']:
        url = stream['url']
        short_url = shorten_url(url)
        button = telebot.types.InlineKeyboardButton(text=url, callback_data=f'del_twitch_{short_url}')
        markup.add(button)
    for stream in config['youtube_streams']:
        video_id = stream['url']
        button = telebot.types.InlineKeyboardButton(text=video_id, callback_data=f'del_youtube_{video_id}')
        markup.add(button)
    for stream in config['qdance_streams']:
        url = stream['url']
        short_url = shorten_url(url)
        button = telebot.types.InlineKeyboardButton(text=url, callback_data=f'del_qdance_{short_url}')
        markup.add(button)
    
    bot.send_message(chat_id, "Select a stream to delete:", reply_markup=markup)

def shorten_url(url):
    return hashlib.md5(url.encode()).hexdigest()

@bot.message_handler(commands=['remove'])
def remove(message):
    if str(message.chat.id) == TELEGRAM_CHAT_ID:
        markup = telebot.types.InlineKeyboardMarkup(row_width=1)
        
        # Erstelle Inline-Buttons für jede Stream-URL
        for stream in config['twitch_streams']:
            url = stream['url']
            short_url = shorten_url(url)
            button = telebot.types.InlineKeyboardButton(text=url, callback_data=f'del_twitch_{short_url}')
            markup.add(button)
        for stream in config['youtube_streams']:
            url = stream['url']
            short_url = shorten_url(url)
            button = telebot.types.InlineKeyboardButton(text=url, callback_data=f'del_youtube_{short_url}')
            markup.add(button)
        for stream in config['qdance_streams']:
            url = stream['url']
            short_url = shorten_url(url)
            button = telebot.types.InlineKeyboardButton(text=url, callback_data=f'del_qdance_{short_url}')
            markup.add(button)
        
        bot.send_message(message.chat.id, "Select a stream to delete:", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "Unauthorized access.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('del_'))
def handle_delete_callback(call):
    _, stream_type, short_url = call.data.split('_', 2)
    
    # Konvertiere den Hash zurück zur Original-URL
    url = next((stream['url'] for stream in config[f'{stream_type}_streams'] if shorten_url(stream['url']) == short_url), None)
    
    if url:
        # Entferne die URL aus der Konfiguration
        config[f'{stream_type}_streams'] = [stream for stream in config[f'{stream_type}_streams'] if stream['url'] != url]
        save_config(config)  # Speichert die aktualisierte Konfiguration
        
        # Bestätige die Löschung
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"Stream URL `{url}` has been deleted.",
            parse_mode='Markdown'
        )
        
        # Zeige das Menü mit den verbleibenden Streams zum Löschen erneut an
        markup = telebot.types.InlineKeyboardMarkup(row_width=1)
        
        # Erstelle Inline-Buttons für jede verbleibende Stream-URL
        for stream in config['twitch_streams']:
            url = stream['url']
            short_url = shorten_url(url)
            button = telebot.types.InlineKeyboardButton(text=url, callback_data=f'del_twitch_{short_url}')
            markup.add(button)
        for stream in config['youtube_streams']:
            url = stream['url']
            short_url = shorten_url(url)
            button = telebot.types.InlineKeyboardButton(text=url, callback_data=f'del_youtube_{short_url}')
            markup.add(button)
        for stream in config['qdance_streams']:
            url = stream['url']
            short_url = shorten_url(url)
            button = telebot.types.InlineKeyboardButton(text=url, callback_data=f'del_qdance_{short_url}')
            markup.add(button)
        
        bot.send_message(call.message.chat.id, "Select a stream to delete:", reply_markup=markup)
        
    else:
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="Failed to find the URL for deletion.",
            parse_mode='Markdown'
        )
    
    bot.answer_callback_query(call.id)

@bot.message_handler(commands=['list_streams'])
def list_streams(message):
    if str(message.chat.id) == TELEGRAM_CHAT_ID:
        response = "Current Streams:\n"
        
        response += "\nTwitch Streams:\n"
        for stream in config['twitch_streams']:
            response += "`{}`\n".format(stream['url'])
        
        response += "\nYouTube Streams:\n"
        for stream in config['youtube_streams']:
            response += "`{}`\n".format(stream['url'])
        
        response += "\nQ-dance Streams:\n"
        for stream in config['qdance_streams']:
            response += "`{}`\n".format(stream['url'])
        
        bot.send_message(message.chat.id, response, parse_mode='Markdown')
    else:
        bot.send_message(message.chat.id, "Unauthorized access.")

@bot.message_handler(commands=['status'])
def status(message):
    if str(message.chat.id) == TELEGRAM_CHAT_ID:
        if not active_recordings:
            bot.send_message(TELEGRAM_CHAT_ID, "No active recordings.")
            return
        
        response = "Active Recordings:\n"
        for url, info in active_recordings.items():
            elapsed_time = datetime.now() - info['start_time']
            response += "`{}` (Type: {})\nStarted: {}\nElapsed Time: {}\n\n".format(
                url, info['type'], info['start_time'].strftime('%Y-%m-%d %H:%M:%S'), str(elapsed_time).split('.')[0])
        
        bot.send_message(TELEGRAM_CHAT_ID, response, parse_mode='Markdown')
    else:
        bot.send_message(message.chat.id, "Unauthorized access.")


@bot.message_handler(commands=['help'])
def help(message):
    if str(message.chat.id) == TELEGRAM_CHAT_ID:
        help_text = (
            "Available Commands:\n"
            "/rec_start - Start recording for all streams listed.\n"
            "/rec_stop - Stop all ongoing recordings.\n"
            "/add - Add a new stream URL. You will be prompted to select the type of stream (Twitch, YouTube, Q-dance).\n"
            "/remove - Delete an existing stream URL. You will be prompted to select the type of stream (Twitch, YouTube, Q-dance).\n"
            "/list_streams - List all currently configured streams.\n"
            "/status - Show the status of ongoing recordings.\n"
            "/help - Display this help message."
        )
        bot.send_message(TELEGRAM_CHAT_ID, help_text)
    else:
        bot.send_message(message.chat.id, "Unauthorized access.")

bot.polling()
