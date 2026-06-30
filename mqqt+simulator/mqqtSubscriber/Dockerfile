FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV LOG_DIR=/app/logs

RUN mkdir -p /app/logs

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY logging_config.py signal_cache.py snapshot.py subscriber.py ./

CMD ["python", "subscriber.py"]
