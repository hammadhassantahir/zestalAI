#!/bin/bash
# Facebook Background Service Cron Job
# This script runs the Facebook background service
# Add this to your crontab to run every hour:
# 0 * * * * /var/www/html/Zestal/zestalAI/facebook_cron.sh

# Set the working directory
cd /var/www/html/Zestal/zestalAI

# Activate virtual environment
source env/bin/activate

# Run the Facebook background service
python app/script/facebook_background_service.py

# Log completion
echo "$(date): Facebook background service completed" >> /var/log/facebook_cron.log
