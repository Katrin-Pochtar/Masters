#!/usr/bin/env python
# pylint: disable=unused-argument
# This program is dedicated to the public domain under the CC0 license.

"""
Cosmic Poetry Bot powered by YandexGPT.
Responds to user messages with cosmic-themed poetry.
Tracks user statistics in a CSV file.
"""

import logging
import os
import csv
import requests
from datetime import datetime
from dotenv import load_dotenv
from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# Load environment variables
load_dotenv()

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
    level=logging.INFO
)
# Set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# Configuration
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OAUTH_TOKEN = os.getenv("YANDEX_OAUTH_TOKEN")
FOLDER_ID = os.getenv("YANDEX_FOLDER_ID")
STATS_FILE = "user_statistics.csv"

# Validate required environment variables
if not all([TOKEN, OAUTH_TOKEN, FOLDER_ID]):
    raise ValueError("Missing required environment variables. Please check your .env file.")

def ensure_stats_file_exists():
    """Ensure the statistics file exists with proper headers."""
    if not os.path.exists(STATS_FILE):
        with open(STATS_FILE, 'w', newline='') as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerow(['user_id', 'timestamp', 'action'])
        logger.info(f"Created new statistics file: {STATS_FILE}")

def log_user_action(user_id: int, action: str):
    """Log user action to the statistics file."""
    try:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(STATS_FILE, 'a', newline='') as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerow([user_id, current_time, action])
        logger.info(f"Logged action for user {user_id}: {action}")
    except Exception as e:
        logger.error(f"Error logging user action: {str(e)}")

def get_iam_token():
    """Get IAM token using OAuth token."""
    try:
        response = requests.post(
            'https://iam.api.cloud.yandex.net/iam/v1/tokens',
            json={'yandexPassportOauthToken': OAUTH_TOKEN}
        )
        response.raise_for_status()
        return response.json()['iamToken']
    except Exception as e:
        logger.error(f"Error getting IAM token: {str(e)}")
        raise

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    logger.info(f"User {user.id} started the bot")
    log_user_action(user.id, "start")
    
    await update.message.reply_html(
        "Приветствую! Я космический поэт с душой YandexGPT. 🌌✨\n"
        "Задайте мне любой вопрос, и я отвечу вам в стихах,\n"
        "Сплетая звезды и галактики в моих поэтических строках! 🚀",
        reply_markup=ForceReply(selective=True),
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    user = update.effective_user
    logger.info(f"User {user.id} requested help")
    log_user_action(user.id, "help")
    
    await update.message.reply_text(
        "Я - космический поэт, вдохновленный YandexGPT! 🌠\n"
        "Просто задайте мне вопрос, и я отвечу вам стихами,\n"
        "Наполненными космической мудростью и красотой.\n\n"
        "Доступные команды:\n"
        "/start - Начать общение\n"
        "/help - Показать это сообщение"
    )

async def process_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process user message using YandexGPT to generate cosmic poetry."""
    user = update.effective_user
    user_text = update.message.text
    logger.info(f"User {user.id} sent message: {user_text}")
    log_user_action(user.id, f"question: {user_text}")

    try:
        # Get IAM token
        iam_token = get_iam_token()
        
        # Prepare cosmic poetry prompt
        cosmic_prompt = f"""Создай поэтический ответ на следующий вопрос: {user_text}

Требования к ответу:
1. Ответ должен быть в стихотворной форме (с рифмой)
2. Должен содержать космические/звездные образы или метафоры
3. Должен быть длиной 2-4 строфы
4. Каждая строфа должна содержать 4 строки
5. Сохраняй информативность, но делай это поэтично

Пожалуйста, предоставь только стихотворение без дополнительного текста."""

        # Prepare request data
        data = {
            "modelUri": f"gpt://{FOLDER_ID}/yandexgpt",
            "completionOptions": {
                "temperature": 0.7,  # Increased for more creative responses
                "maxTokens": 1000
            },
            "messages": [
                {"role": "user", "text": cosmic_prompt}
            ]
        }

        # Send request to YandexGPT
        response = requests.post(
            "https://llm.api.cloud.yandex.net/foundationModels/v1/completion",
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {iam_token}"
            },
            json=data
        )
        response.raise_for_status()
        response_data = response.json()

        # Extract answer from response
        answer = response_data.get('result', {})\
                            .get('alternatives', [{}])[0]\
                            .get('message', {})\
                            .get('text', "Извините, не удалось создать стихотворение.")

        await update.message.reply_text(answer)
        log_user_action(user.id, "answer")
        logger.info(f"Sent cosmic poetry response to user {user.id}")

    except Exception as e:
        logger.error(f"Error processing message: {str(e)}", exc_info=True)
        await update.message.reply_text("Извините, произошла ошибка при создании стихотворения.")
        log_user_action(user.id, "error")

def main() -> None:
    """Start the bot."""
    try:
        # Ensure stats file exists
        ensure_stats_file_exists()
        logger.info("Statistics file checked")

        # Create the Application and pass it your bot's token
        application = Application.builder().token(TOKEN).build()
        logger.info("Application created successfully")

        # Add command handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))

        # Add message handler
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_message))
        logger.info("Handlers added")

        # Run the bot until the user presses Ctrl-C
        logger.info("Starting bot...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        logger.error(f"Error starting bot: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()