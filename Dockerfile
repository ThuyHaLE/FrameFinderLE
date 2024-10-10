# Use an official Python runtime as a parent image
FROM python:3.10.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies, including git
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    software-properties-common \
    unzip \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install gdown
RUN pip install --no-cache-dir gdown

# Set work directory
WORKDIR /app/FrameFinderLE

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Download spacy language model
RUN python -m spacy download en_core_web_sm

# Download NLTK 'punkt' resource
RUN python -m nltk.downloader punkt

# Copy the download script
COPY download_files.sh .

# Make the script executable
RUN chmod +x download_files.sh

# Copy the entire project
COPY . .

# Run the download script
RUN ./download_files.sh

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application with hot reloading
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]