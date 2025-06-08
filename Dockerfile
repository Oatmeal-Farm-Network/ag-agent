#  Using 3.10-slim 
FROM python:3.10-slim

# Setting the working directory inside the container to /app
WORKDIR /app

# Copying the dependencies file first. which helps Docker's caching mechanism.
COPY requirements.txt .

# Installing all the dependencies from requirements file.
RUN pip install --no-cache-dir -r requirements.txt

# Copying all your project files and folders into the container's /app directory.
# This includes app.py, config.py, utils.py, and all your module folders.
COPY . .

# Telling Docker what command to run when the container starts.
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]