FROM python:3.11-slim

WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV FLASK_RUN_HOST=0.0.0.0
ENV PORT=8000

# Copy the requirements file into the container at /app
COPY requirements.txt ./

# Install packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code from the Backend directory into the container at /app
COPY . .

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Run the app
CMD ["python", "app.py"]