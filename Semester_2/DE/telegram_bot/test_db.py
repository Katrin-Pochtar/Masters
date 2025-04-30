from database import init_db, SessionLocal
from sqlalchemy import text, create_engine
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Database configuration
DB_USER = os.getenv("DB_USER", "telegram_bot")
DB_PASSWORD = os.getenv("DB_PASSWORD", "tg_bot_secure_pass_2024")
DB_HOST = os.getenv("DB_HOST", "172.18.0.2")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "telegram_stats")

# Create database URL
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

logger.info(f"Connecting to database at {DB_HOST}:{DB_PORT} as {DB_USER}")

def test_database():
    try:
        # Initialize database
        logger.info("Initializing database...")
        init_db()
        
        # Create a session
        db = SessionLocal()
        
        # Check existing tables
        logger.info("Checking existing tables...")
        result = db.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
        print("\nExisting tables:")
        for row in result:
            print(f"- {row[0]}")
            
        # Check user_actions table
        logger.info("\nChecking user_actions table...")
        result = db.execute(text("SELECT COUNT(*) FROM user_actions"))
        count = result.scalar()
        print(f"Number of records in user_actions: {count}")
        
        # Check user_info table
        logger.info("\nChecking user_info table...")
        result = db.execute(text("SELECT COUNT(*) FROM user_info"))
        count = result.scalar()
        print(f"Number of records in user_info: {count}")
        
        db.close()
        logger.info("Database test completed successfully")
        
    except Exception as e:
        logger.error(f"Error during database test: {str(e)}")
        raise

if __name__ == "__main__":
    test_database() 