#!/usr/bin/env python
# pylint: disable=unused-argument
# This program is dedicated to the public domain under the CC0 license.

"""
Cosmic Poetry Bot powered by YandexGPT.
Responds to user messages with cosmic-themed poetry.
Tracks user statistics in a PostgreSQL database.
"""

import logging
import os
import aiohttp
from datetime import datetime
from dotenv import load_dotenv
from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
import psycopg2
import asyncio

from database import init_db, log_user_action, log_user_info, SessionLocal, UserInfo, QAPair, update_datalens_analytics
from sqlalchemy import text

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

# Database Configuration
DB_NAME = os.getenv("DB_NAME", "telegram_stats")
DB_USER = os.getenv("DB_USER", "telegram_bot")
DB_PASSWORD = os.getenv("DB_PASSWORD", "tg_bot_secure_pass_2024")
DB_HOST = os.getenv("DB_HOST", "172.18.0.2")
DB_PORT = os.getenv("DB_PORT", "5432")

# Validate required environment variables
if not all([TOKEN, OAUTH_TOKEN, FOLDER_ID]):
    raise ValueError("Missing required environment variables. Please check your .env file.")

async def get_iam_token():
    """Get IAM token using OAuth token."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                'https://iam.api.cloud.yandex.net/iam/v1/tokens',
                json={'yandexPassportOauthToken': OAUTH_TOKEN}
            ) as response:
                response.raise_for_status()
                data = await response.json()
                return data['iamToken']
    except Exception as e:
        logger.error(f"Error getting IAM token: {str(e)}")
        raise

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    logger.info(f"User {user.id} started the bot")
    
    # Log user information including language code
    log_user_info(user.id, language_code=user.language_code)
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
    
    # Update user information if language code changes
    try:
        log_user_info(user.id, language_code=user.language_code)
        logger.info(f"Updated user info for {user.id}: language_code={user.language_code}")
    except Exception as e:
        logger.error(f"Error updating user info: {str(e)}")

    try:
        log_user_action(user.id, f"question: {user_text}")
        logger.info(f"Logged question action for user {user.id}")
    except Exception as e:
        logger.error(f"Error logging user action: {str(e)}")

    try:
        # Get IAM token
        iam_token = await get_iam_token()
        
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
                "temperature": 0.7,
                "maxTokens": 1000
            },
            "messages": [
                {"role": "user", "text": cosmic_prompt}
            ]
        }

        # Send request to YandexGPT
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://llm.api.cloud.yandex.net/foundationModels/v1/completion",
                headers={
                    "Accept": "application/json",
                    "Authorization": f"Bearer {iam_token}"
                },
                json=data
            ) as response:
                response.raise_for_status()
                response_data = await response.json()

        # Extract answer from response
        answer = response_data.get('result', {})\
                            .get('alternatives', [{}])[0]\
                            .get('message', {})\
                            .get('text', "Извините, не удалось создать стихотворение.")

        # Store Q&A pair in database
        db = SessionLocal()
        try:
            # Ensure user exists in user_info
            user_info = db.query(UserInfo).filter(UserInfo.user_id == user.id).first()
            if not user_info:
                user_info = UserInfo(
                    user_id=user.id,
                    language_code=user.language_code
                )
                db.add(user_info)
                db.commit()
                logger.info(f"Created new user_info entry for user {user.id}")

            # Store Q&A pair
            qa_pair = QAPair(
                user_id=user.id,
                question=user_text,
                answer=answer
            )
            db.add(qa_pair)
            db.commit()
            logger.info(f"Stored Q&A pair for user {user.id}")
        except Exception as e:
            db.rollback()
            logger.error(f"Error storing Q&A pair: {str(e)}")
        finally:
            db.close()

        await update.message.reply_text(answer)
        log_user_action(user.id, "answer")
        logger.info(f"Sent cosmic poetry response to user {user.id}")

    except Exception as e:
        logger.error(f"Error processing message: {str(e)}", exc_info=True)
        await update.message.reply_text("Извините, произошла ошибка при создании стихотворения.")
        log_user_action(user.id, f"error: {str(e)}")

async def log_user_action(user_id: int, action: str):
    """Log user action to database"""
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        logging.info(f"Successfully connected to database at {DB_HOST}:{DB_PORT}")
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO user_actions (user_id, action, timestamp) VALUES (%s, %s, NOW())",
            (user_id, action)
        )
        conn.commit()
        logging.info(f"Successfully logged action for user {user_id}: {action}")
        cur.close()
        conn.close()
    except Exception as e:
        logging.error(f"Error logging user action: {str(e)}")
        raise

async def log_user_info(user_id: int, language_code: str):
    """Log user information to database"""
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        logging.info(f"Successfully connected to database at {DB_HOST}:{DB_PORT}")
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO user_info (user_id, language_code) VALUES (%s, %s) ON CONFLICT (user_id) DO UPDATE SET language_code = %s",
            (user_id, language_code, language_code)
        )
        conn.commit()
        logging.info(f"Successfully logged/updated info for user {user_id}")
        cur.close()
        conn.close()
    except Exception as e:
        logging.error(f"Error logging user info: {str(e)}")
        raise

async def update_analytics_periodically():
    """Update DataLens analytics table every 5 minutes."""
    logger.info("Starting periodic analytics update task...")
    while True:
        try:
            logger.info("Running analytics update...")
            update_datalens_analytics()
            logger.info("Analytics update completed successfully")
            await asyncio.sleep(300)  # Sleep for 5 minutes
        except Exception as e:
            logger.error(f"Error in periodic analytics update: {str(e)}", exc_info=True)
            await asyncio.sleep(60)  # If error occurs, retry after 1 minute

async def main() -> None:
    """Start the bot."""
    # Initialize database
    init_db()
    logger.info("Database initialized")

    # Create the Application and pass it your bot's token
    application = Application.builder().token(TOKEN).build()
    logger.info("Application created successfully")

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    # Add message handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_message))
    logger.info("Handlers added")

    # Start analytics update task
    analytics_task = asyncio.create_task(update_analytics_periodically())
    logger.info("Analytics update task started")

    # Run the bot until the user presses Ctrl-C
    logger.info("Starting bot...")
    await application.initialize()
    await application.start()
    await application.run_polling(allowed_updates=Update.ALL_TYPES)
    
    # Wait for the analytics task to complete (it won't, but this ensures proper cleanup)
    await analytics_task

if __name__ == "__main__":
    asyncio.run(main())