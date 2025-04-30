#!/usr/bin/env python
import os
import pandas as pd
import psycopg2
from datetime import datetime
import logging
from dotenv import load_dotenv

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
DB_HOST = "51.250.111.135"  # Server IP address
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "telegram_stats")

def check_table_counts(conn):
    """Check row counts for each table."""
    tables = [
        'user_info',
        'user_actions',
        'qa_pairs',
        'datalens_analytics',
        'user_actions_stats',
        'detailed_qa_stats'
    ]
    
    print("\nTable Row Counts:")
    print("-----------------")
    for table in tables:
        try:
            cur = conn.cursor()
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            count = cur.fetchone()[0]
            print(f"{table}: {count} rows")
            cur.close()
        except Exception as e:
            print(f"Error checking {table}: {str(e)}")

def export_logs_to_excel():
    """Export logs from database to Excel file."""
    try:
        # Connect to database
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        logger.info("Successfully connected to database")
        
        # Check table counts
        check_table_counts(conn)
        
        # Get current timestamp for filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        excel_filename = f"telegram_bot_logs_{timestamp}.xlsx"
        
        # Create Excel writer
        with pd.ExcelWriter(excel_filename, engine='openpyxl') as writer:
            # Export user_info
            logger.info("Exporting user_info...")
            user_info_df = pd.read_sql_query("SELECT * FROM user_info", conn)
            user_info_df.to_excel(writer, sheet_name='User Info', index=False)
            
            # Export user_actions
            logger.info("Exporting user_actions...")
            user_actions_df = pd.read_sql_query("SELECT * FROM user_actions", conn)
            user_actions_df.to_excel(writer, sheet_name='User Actions', index=False)
            
            # Export qa_pairs
            logger.info("Exporting qa_pairs...")
            qa_pairs_df = pd.read_sql_query("SELECT * FROM qa_pairs", conn)
            qa_pairs_df.to_excel(writer, sheet_name='Q&A Pairs', index=False)
            
            # Export datalens_analytics
            logger.info("Exporting datalens_analytics...")
            analytics_df = pd.read_sql_query("SELECT * FROM datalens_analytics", conn)
            analytics_df.to_excel(writer, sheet_name='Analytics', index=False)
            
            # Export user_actions_stats view
            logger.info("Exporting user_actions_stats...")
            stats_df = pd.read_sql_query("SELECT * FROM user_actions_stats", conn)
            stats_df.to_excel(writer, sheet_name='Action Stats', index=False)
            
            # Export detailed_qa_stats view
            logger.info("Exporting detailed_qa_stats...")
            qa_stats_df = pd.read_sql_query("SELECT * FROM detailed_qa_stats", conn)
            qa_stats_df.to_excel(writer, sheet_name='Detailed Q&A Stats', index=False)
        
        logger.info(f"Successfully exported logs to {excel_filename}")
        return excel_filename
        
    except Exception as e:
        logger.error(f"Error exporting logs: {str(e)}", exc_info=True)
        raise
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    try:
        excel_file = export_logs_to_excel()
        print(f"Logs exported successfully to: {excel_file}")
    except Exception as e:
        print(f"Error exporting logs: {str(e)}") 