FROM python:3.13-slim

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app.py .

# Create data directory
RUN mkdir -p /app/data

EXPOSE 8503
EXPOSE 8004

CMD ["streamlit", "run", "app.py", "--server.port=8503", "--server.address=0.0.0.0"]