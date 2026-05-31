# # Dockerfile

# FROM python:3.11-slim

# WORKDIR /app

# # install dependencies
# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt

# # copy project
# COPY . .

# # run app
# CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

# Install supervisor to manage multiple processes
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y supervisor

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

CMD ["supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]