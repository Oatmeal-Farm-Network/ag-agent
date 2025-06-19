# ---- STAGE 1: The Builder ----
# This stage will install all dependencies using a constraints file to control torch.
FROM python:3.10-slim AS builder

WORKDIR /app

# Create a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy both requirements and the new constraints file
COPY requirements.txt .
COPY constraints.txt .

# Install all dependencies at once.
# The "-c constraints.txt" flag tells pip to obey the rules in our new file.
RUN pip install --no-cache-dir -r requirements.txt -c constraints.txt

RUN pip uninstall -y pyarrow


# ---- STAGE 2: The Final Image ----
# This stage will be our lean, production image and remains unchanged.
FROM python:3.10-slim

WORKDIR /app

# Copy only the clean (and now much smaller) virtual environment
COPY --from=builder /opt/venv /opt/venv

# Copy your application code
COPY . .

# Activate the virtual environment by setting the PATH
ENV PATH="/opt/venv/bin:$PATH"

# Expose the port Streamlit will run on
EXPOSE 8000

# The command to run your Streamlit app
CMD ["streamlit", "run", "app.py", "--server.port=8000", "--server.address=0.0.0.0"]