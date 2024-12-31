# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Install system dependencies
# For pydub to work properly, you need ffmpeg or libav.
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Create a working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the files
COPY . /app

# Expose any port if needed (not really needed if we only generate files)
# EXPOSE 8000

# Command to run the application
CMD ["python", "focus_app.py"]
