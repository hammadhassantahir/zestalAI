#!/bin/bash

echo "Stopping Flask server..."
pkill -f "python.*wsgi.py" || true
pkill -f "flask run" || true

echo "Waiting for processes to stop..."
sleep 2

echo "Starting Flask server..."
cd /var/www/html/zestalAI
python3 wsgi.py &

echo "Flask server restarted with new CORS configuration!"
echo "Check the logs to ensure it's running properly."
