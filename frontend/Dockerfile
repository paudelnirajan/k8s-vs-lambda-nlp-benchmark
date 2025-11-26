FROM python:3.9-slim

WORKDIR /app

# Install system dependencies for heavy python packages if needed
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY frontend/requirements.txt requirements.txt
# Install dependencies (Streamlit, Locust, etc.)
RUN pip install --no-cache-dir -r requirements.txt

# Copy the whole project (needed for scripts/locustfile)
COPY . .

# Expose Streamlit port
EXPOSE 8501

# Run app
CMD ["streamlit", "run", "frontend/app.py", "--server.port=8501", "--server.address=0.0.0.0"]