FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy the project files into the container
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Add a wait-for-it script to wait for the database
RUN apt-get update && apt-get install -y netcat && \
    echo '#!/bin/sh\nwhile ! nc -z postgres 5432; do sleep 1; done\nexec "$@"' > /wait-for-it.sh && \
    chmod +x /wait-for-it.sh

# Set the default command to wait for the database and run the scraper
CMD ["/wait-for-it.sh", "python", "main.py"]
