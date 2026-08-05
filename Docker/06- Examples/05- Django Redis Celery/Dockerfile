FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y gcc curl netcat-openbsd && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ .
COPY scripts/start_web.sh /start_web.sh
COPY scripts/start_worker.sh /start_worker.sh

RUN chmod +x /start_web.sh /start_worker.sh

EXPOSE 8000

CMD ["/start_web.sh"]
