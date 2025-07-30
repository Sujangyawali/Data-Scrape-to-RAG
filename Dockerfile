# Use an official Python runtime as the base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements-local.txt .
RUN pip install --no-cache-dir -r requirements-local.txt

# Create the directory inside the image to avoid volume permission issues
RUN mkdir -p /app/data/silver 

# Expose the port the app runs on
EXPOSE 8000 8501

# Copy entrypoint
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh