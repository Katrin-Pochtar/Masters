import os
import yadisk
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Config
CSV_STATS_FILE = "user_statistics.csv"
EXCEL_STATS_FILE = "user_statistics.xlsx"
YANDEX_DISK_TOKEN = os.getenv("YANDEX_DISK_TOKEN")

# Validate required environment variables
if not YANDEX_DISK_TOKEN:
    raise ValueError("YANDEX_DISK_TOKEN not found in .env file")

def convert_csv_to_excel(csv_file, excel_file):
    df = pd.read_csv(csv_file, delimiter=';')
    df.to_excel(excel_file, index=False)
    print(f"Converted {csv_file} to {excel_file}")

def upload_to_yadisk(local_file, remote_path):
    y = yadisk.YaDisk(token=YANDEX_DISK_TOKEN)
    
    # Check connection
    if not y.check_token():
        raise ValueError("Invalid Yandex Disk token")

    # Upload file
    y.upload(local_file, remote_path, overwrite=True)
    print(f"Uploaded {local_file} to Yandex Disk at {remote_path}")

if __name__ == "__main__":
    if not os.path.exists(CSV_STATS_FILE):
        raise FileNotFoundError(f"{CSV_STATS_FILE} not found!")

    # Convert CSV to Excel
    convert_csv_to_excel(CSV_STATS_FILE, EXCEL_STATS_FILE)

    # Set remote path (folder/file) on Yandex Disk
    today = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    remote_file_path = f"/bot_statistics/user_statistics.xlsx"

    # Upload Excel to Yandex Disk
    upload_to_yadisk(EXCEL_STATS_FILE, remote_file_path)
