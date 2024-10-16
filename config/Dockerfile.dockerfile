# Use an official Python runtime as the base image
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install required Python packages
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port the Dash app will run on
EXPOSE 8050

# Command to run the Dash app
CMD ["python", "app.py"]
