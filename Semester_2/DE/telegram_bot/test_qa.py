import os
import requests
import psycopg2
from datetime import datetime, timedelta
from dotenv import load_dotenv
import time

load_dotenv()

# Telegram Bot configuration
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = "216786311"  # Your chat ID

# Database configuration
DB_USER = os.getenv("DB_USER", "telegram_bot")
DB_PASSWORD = os.getenv("DB_PASSWORD", "tg_bot_secure_pass_2024")
DB_HOST = os.getenv("DB_HOST", "postgres")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "telegram_stats")

def send_test_question():
    """Send a test question to the bot."""
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    test_question = "Что такое космическая поэзия?"
    
    data = {
        "chat_id": CHAT_ID,
        "text": test_question
    }
    
    print(f"Sending test question: {test_question}")
    response = requests.post(url, json=data)
    print(f"Response status: {response.status_code}")
    print(f"Response: {response.json()}")
    return test_question

def check_database_entries(question):
    """Check database entries for the test question and answer."""
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    
    try:
        with conn.cursor() as cur:
            # Wait a bit for the bot to process and store the response
            time.sleep(5)
            
            # Check recent entries
            cur.execute("""
                SELECT timestamp, action 
                FROM user_actions 
                WHERE timestamp >= NOW() - INTERVAL '1 minute'
                ORDER BY timestamp DESC;
            """)
            
            print("\nRecent database entries:")
            print("-" * 50)
            entries = cur.fetchall()
            for entry in entries:
                print(f"Time: {entry[0]}, Action: {entry[1]}")
            
            # Check materialized view
            cur.execute("""
                SELECT user_id, hour, questions, answers
                FROM user_actions_stats
                WHERE hour >= NOW() - INTERVAL '1 hour'
                ORDER BY hour DESC;
            """)
            
            print("\nMaterialized view entries:")
            print("-" * 50)
            stats = cur.fetchall()
            for stat in stats:
                print(f"User: {stat[0]}, Hour: {stat[1]}")
                print(f"Questions: {stat[2]}")
                print(f"Answers: {stat[3]}")
                print("-" * 30)
                
    finally:
        conn.close()

if __name__ == "__main__":
    print("Starting test...")
    question = send_test_question()
    print("\nWaiting for bot to process the message...")
    time.sleep(2)  # Wait for bot to process
    check_database_entries(question) 