import yadisk
import tempfile
import os
import csv

# Initialize the client with your token
y = yadisk.YaDisk(token="y0__xDaoO2kqveAAhigkzcg3unI7xLU6bexyLmAbp5RAYX8CN1Z3dn8mw")

# Path to the statistics file
STATS_FILE = "/user_statistics.csv"

# Create a temporary file
temp_file = os.path.join(tempfile.gettempdir(), "temp_stats.csv")

try:
    # Download the file
    y.download(STATS_FILE, temp_file)
    
    # Read and print its contents
    print("Contents of statistics file:")
    print("-" * 50)
    with open(temp_file, 'r') as f:
        print(f.read())
    
    # Remove temporary file
    os.remove(temp_file)
except Exception as e:
    print(f"Error reading statistics: {e}") 