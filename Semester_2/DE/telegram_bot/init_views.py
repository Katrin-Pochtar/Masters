from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()

# Database configuration
DB_USER = os.getenv("DB_USER", "telegram_bot")
DB_PASSWORD = os.getenv("DB_PASSWORD", "tg_bot_secure_pass_2024")
DB_HOST = os.getenv("DB_HOST", "postgres")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "telegram_stats")

# Create database URL
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def init_views():
    """Initialize the database views for DataLens integration."""
    engine = create_engine(DATABASE_URL)
    
    try:
        # Drop existing objects if they exist
        with engine.connect() as connection:
            # Check if user_actions_stats exists and what type it is
            result = connection.execute(text("""
                SELECT table_type 
                FROM information_schema.tables 
                WHERE table_name = 'user_actions_stats'
            """))
            table_info = result.fetchone()
            
            if table_info:
                print(f"Found existing user_actions_stats of type: {table_info[0]}")
                connection.execute(text("DROP TABLE IF EXISTS user_actions_stats CASCADE"))
                connection.execute(text("DROP VIEW IF EXISTS user_actions_stats CASCADE"))
                print("Dropped existing user_actions_stats")
                
            # Do the same for detailed_qa_stats
            result = connection.execute(text("""
                SELECT table_type 
                FROM information_schema.tables 
                WHERE table_name = 'detailed_qa_stats'
            """))
            table_info = result.fetchone()
            
            if table_info:
                print(f"Found existing detailed_qa_stats of type: {table_info[0]}")
                connection.execute(text("DROP TABLE IF EXISTS detailed_qa_stats CASCADE"))
                connection.execute(text("DROP VIEW IF EXISTS detailed_qa_stats CASCADE"))
                print("Dropped existing detailed_qa_stats")
                
            connection.commit()
            
        # Read the SQL file
        with open('init_views.sql', 'r') as file:
            sql = file.read()
            
        # Execute the SQL statements
        with engine.connect() as connection:
            connection.execute(text(sql))
            connection.commit()
            
        print("Views created successfully!")
        
        # Verify the views exist and show sample data
        with engine.connect() as connection:
            # Check user_actions_stats
            result = connection.execute(text("""
                SELECT COUNT(*) 
                FROM user_actions_stats
            """))
            count = result.scalar()
            print(f"user_actions_stats has {count} rows")
            
            # Show sample data from user_actions_stats
            result = connection.execute(text("""
                SELECT * FROM user_actions_stats LIMIT 3
            """))
            print("\nSample data from user_actions_stats:")
            for row in result:
                print(row)
            
            # Check detailed_qa_stats
            result = connection.execute(text("""
                SELECT COUNT(*) 
                FROM detailed_qa_stats
            """))
            count = result.scalar()
            print(f"\ndetailed_qa_stats has {count} rows")
            
            # Show sample data from detailed_qa_stats
            result = connection.execute(text("""
                SELECT * FROM detailed_qa_stats LIMIT 3
            """))
            print("\nSample data from detailed_qa_stats:")
            for row in result:
                print(row)
            
    except Exception as e:
        print(f"Error initializing views: {e}")

if __name__ == "__main__":
    init_views() 