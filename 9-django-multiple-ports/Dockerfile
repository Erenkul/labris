FROM python:3.12-slim
RUN apt-get update && apt-get install -y default-libmysqlclient-dev build-essential pkg-config
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
