FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Make the upload script executable
RUN chmod +x upload_stats.sh

# Set up cron for periodic uploads
RUN apt-get update && apt-get install -y cron \
    && rm -rf /var/lib/apt/lists/*

# Add cron job
RUN echo "0 0 * * * /app/upload_stats.sh >> /app/upload_stats.log 2>&1" > /etc/cron.d/upload-stats
RUN chmod 0644 /etc/cron.d/upload-stats

# Start cron in the background and run the bot
CMD cron && python cosmo_bot.py 