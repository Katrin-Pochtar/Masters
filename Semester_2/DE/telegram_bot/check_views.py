from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

load_dotenv()

# Database configuration - Update these with your Yandex Cloud database details
DB_USER = os.getenv("DB_USER", "telegram_bot")
DB_PASSWORD = os.getenv("DB_PASSWORD", "tg_bot_secure_pass_2024")
DB_HOST = os.getenv("DB_HOST", "rc1a-abcdefghijkl.mdb.yandexcloud.net")  # Replace with your actual Yandex Cloud host
DB_PORT = os.getenv("DB_PORT", "6432")  # Default Yandex Cloud port
DB_NAME = os.getenv("DB_NAME", "telegram_stats")

# Create database URL with SSL parameters for Yandex Cloud
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode=require"

def check_views():
    """Check if views exist and show their contents."""
    engine = create_engine(DATABASE_URL)
    
    try:
        with engine.connect() as connection:
            # Check if views exist
            result = connection.execute(text("""
                SELECT table_schema, table_name, table_type 
                FROM information_schema.tables 
                WHERE table_name IN ('user_actions_stats', 'detailed_qa_stats', 'user_actions_detailed')
                AND table_type = 'VIEW'
            """))
            
            print("\nExisting views:")
            print("-" * 50)
            for row in result:
                print(f"Schema: {row[0]}, Name: {row[1]}, Type: {row[2]}")
            
            # Check user_actions_detailed view
            result = connection.execute(text("""
                SELECT COUNT(*) 
                FROM user_actions_detailed
            """))
            count = result.scalar()
            print(f"\nNumber of records in user_actions_detailed: {count}")
            
            # Show sample data from user_actions_detailed
            result = connection.execute(text("""
                SELECT * FROM user_actions_detailed LIMIT 5
            """))
            print("\nSample data from user_actions_detailed:")
            print("-" * 50)
            for row in result:
                print(row)
            
            # Check if the view definition matches what we expect
            result = connection.execute(text("""
                SELECT view_definition 
                FROM information_schema.views 
                WHERE table_name = 'user_actions_detailed'
            """))
            print("\nView definition:")
            print("-" * 50)
            for row in result:
                print(row[0])
                
    except Exception as e:
        logger.error(f"Error checking views: {str(e)}")
        raise

if __name__ == "__main__":
    check_views() 