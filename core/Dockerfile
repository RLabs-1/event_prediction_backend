# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory
WORKDIR /app

# Copy the current directory into the container
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose Django's default port
EXPOSE 8000

# Command to run Django server (replace `yourproject` with your actual project folder)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
