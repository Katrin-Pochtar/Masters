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

# Database configuration
DB_USER = os.getenv("DB_USER", "telegram_bot")
DB_PASSWORD = os.getenv("DB_PASSWORD", "tg_bot_secure_pass_2024")
DB_HOST = os.getenv("DB_HOST")  # Get from .env
DB_PORT = os.getenv("DB_PORT")  # Get from .env
DB_NAME = os.getenv("DB_NAME", "telegram_stats")

# Create database URL
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def create_view():
    """Create the user_actions_detailed view."""
    # Read the SQL file
    with open('create_view.sql', 'r') as file:
        sql = file.read()
    
    # Create engine and execute SQL
    engine = create_engine(DATABASE_URL)
    try:
        with engine.connect() as conn:
            # Create the view
            conn.execute(text(sql))
            conn.commit()
            logger.info("View created successfully")
            
            # Verify the view exists
            result = conn.execute(text("""
                SELECT table_schema, table_name 
                FROM information_schema.views 
                WHERE table_name = 'user_actions_detailed'
            """))
            views = list(result)
            if views:
                logger.info(f"View exists in schema: {views[0][0]}")
                
                # Check if view has data
                result = conn.execute(text("SELECT COUNT(*) FROM user_actions_detailed"))
                count = result.scalar()
                logger.info(f"View contains {count} records")
                
                # Show sample data
                result = conn.execute(text("SELECT * FROM user_actions_detailed LIMIT 3"))
                logger.info("Sample data:")
                for row in result:
                    logger.info(row)
            else:
                logger.error("View was not created successfully")
                
    except Exception as e:
        logger.error(f"Error creating view: {str(e)}")
        raise

if __name__ == "__main__":
    create_view() 