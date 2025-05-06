# Use the official Python image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy dependencies file
COPY ../requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the user_management app code
COPY . .

# Run migrations and start the server 
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
