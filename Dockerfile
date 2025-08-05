# Start with the official Python image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file and install dependencies
# This layer is cached to speed up future builds
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Install runtime dependencies (ffmpeg) for audio processing
# and Microsoft ODBC Driver for SQL Server
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    gnupg2 \
    unixodbc-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Microsoft ODBC Driver for SQL Server
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && \
    curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update && \
    ACCEPT_EULA=Y apt-get install -y msodbcsql18 && \
    rm -rf /var/lib/apt/lists/*

# Health check to ensure the application is running
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Copy your application code into the container
COPY . .

# Expose the port the app will run on
EXPOSE 8000

# Command to run the application using Gunicorn and Uvicorn
# This is the standard for production FastAPI.
# It assumes your main file is 'backend.py' and your FastAPI instance is 'app'
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "backend:app", "--bind", "0.0.0.0:8000"]