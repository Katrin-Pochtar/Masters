from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv
import time
from datetime import datetime, timedelta

load_dotenv()

# Database configuration
DB_USER = os.getenv("DB_USER", "telegram_bot")
DB_PASSWORD = os.getenv("DB_PASSWORD", "tg_bot_secure_pass_2024")
DB_HOST = os.getenv("DB_HOST", "postgres")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "telegram_stats")

# Create database URL
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def check_stats_freshness():
    """Check if statistics are being updated in real-time."""
    engine = create_engine(DATABASE_URL)
    
    try:
        with engine.connect() as connection:
            # Check last update time
            result = connection.execute(text("""
                SELECT MAX(hour) as last_update
                FROM user_actions_stats
            """))
            last_update = result.fetchone()[0]
            
            if last_update:
                now = datetime.utcnow()
                delay = now - last_update
                print(f"Last update: {last_update}")
                print(f"Current delay: {delay}")
                
                # Get recent statistics
                result = connection.execute(text("""
                    SELECT 
                        user_id,
                        hour,
                        action_count,
                        questions_count,
                        answers_count,
                        errors_count
                    FROM user_actions_stats
                    WHERE hour >= NOW() - INTERVAL '1 day'
                    ORDER BY hour DESC
                    LIMIT 5
                """))
                
                print("\nRecent statistics:")
                print("User ID | Hour | Actions | Questions | Answers | Errors")
                print("-" * 60)
                
                for row in result:
                    print(f"{row.user_id:7d} | {row.hour} | {row.action_count:8d} | {row.questions_count:9d} | {row.answers_count:7d} | {row.errors_count:6d}")
            else:
                print("No statistics available yet")
                
    except Exception as e:
        print(f"Error checking statistics: {e}")

if __name__ == "__main__":
    while True:
        print("\nChecking statistics freshness...")
        check_stats_freshness()
        print("\nWaiting 60 seconds before next check...")
        time.sleep(60) 