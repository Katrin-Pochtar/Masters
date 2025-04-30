#!/usr/bin/env python
"""
Script to upload bot statistics to Yandex Disk and prepare for DataLens visualization.
"""

import os
import logging
import pandas as pd
from datetime import datetime
from yadisk import YaDisk
from dotenv import load_dotenv
import psycopg2
from sqlalchemy import create_engine

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Database configuration
DB_USER = os.getenv("DB_USER", "telegram_bot")
DB_PASSWORD = os.getenv("DB_PASSWORD", "tg_bot_secure_pass_2024")
DB_HOST = os.getenv("DB_HOST", "172.18.0.2")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "telegram_stats")

# Yandex Disk configuration
YANDEX_TOKEN = os.getenv("YANDEX_DISK_TOKEN")
DISK_FOLDER = "/telegram_bot_stats"

def get_stats_from_db():
    """Retrieve statistics from the database."""
    try:
        # Create database connection
        engine = create_engine(
            f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        )
        
        # Query user actions statistics
        user_actions_query = """
            SELECT 
                ua.user_id,
                ua.timestamp,
                ua.action,
                ui.language_code,
                ui.country,
                ui.first_seen
            FROM user_actions ua
            LEFT JOIN user_info ui ON ua.user_id = ui.user_id
            ORDER BY ua.timestamp DESC
        """
        
        # Query Q&A statistics
        qa_query = """
            SELECT 
                qp.user_id,
                qp.question,
                qp.answer,
                qp.timestamp,
                ui.language_code,
                ui.country
            FROM qa_pairs qp
            LEFT JOIN user_info ui ON qp.user_id = ui.user_id
            ORDER BY qp.timestamp DESC
        """
        
        # Execute queries and convert to DataFrames
        user_actions_df = pd.read_sql(user_actions_query, engine)
        qa_df = pd.read_sql(qa_query, engine)
        
        logger.info(f"Retrieved {len(user_actions_df)} user actions and {len(qa_df)} Q&A pairs")
        return user_actions_df, qa_df
        
    except Exception as e:
        logger.error(f"Error retrieving statistics from database: {str(e)}")
        raise

def upload_to_yandex_disk(user_actions_df, qa_df):
    """Upload statistics to Yandex Disk."""
    try:
        # Initialize Yandex Disk client
        yadisk = YaDisk(token=YANDEX_TOKEN)
        
        # Create folder if it doesn't exist
        if not yadisk.exists(DISK_FOLDER):
            yadisk.mkdir(DISK_FOLDER)
        
        # Generate filenames with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        user_actions_file = f"user_actions_{timestamp}.xlsx"
        qa_file = f"qa_pairs_{timestamp}.xlsx"
        
        # Save DataFrames to Excel files
        user_actions_df.to_excel(user_actions_file, index=False)
        qa_df.to_excel(qa_file, index=False)
        
        # Upload files to Yandex Disk
        yadisk.upload(user_actions_file, f"{DISK_FOLDER}/{user_actions_file}")
        yadisk.upload(qa_file, f"{DISK_FOLDER}/{qa_file}")
        
        logger.info(f"Successfully uploaded files to Yandex Disk: {user_actions_file}, {qa_file}")
        
        # Clean up local files
        os.remove(user_actions_file)
        os.remove(qa_file)
        
    except Exception as e:
        logger.error(f"Error uploading to Yandex Disk: {str(e)}")
        raise

def main():
    """Main function to execute the upload process."""
    try:
        logger.info("Starting statistics upload process...")
        
        # Get statistics from database
        user_actions_df, qa_df = get_stats_from_db()
        
        # Upload to Yandex Disk
        upload_to_yandex_disk(user_actions_df, qa_df)
        
        logger.info("Statistics upload process completed successfully")
        
    except Exception as e:
        logger.error(f"Error in main process: {str(e)}")
        raise

if __name__ == "__main__":
    main() 