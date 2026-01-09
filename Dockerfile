FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    libssl-dev \
    libffi-dev \
    python3-dev \
    nginx \
    supervisor \
    gettext-base \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN python -m venv /opt/venv \
    && . /opt/venv/bin/activate \
    && pip install --upgrade pip setuptools wheel \
    && pip install -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=backend.settings
ENV PATH="/opt/venv/bin:$PATH"

RUN . /opt/venv/bin/activate && python manage.py collectstatic --noinput

COPY nginx.conf /etc/nginx/nginx.conf.template
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

ENV PORT=8000
EXPOSE 8000

CMD ["/bin/sh", "-c", "\
  . /opt/venv/bin/activate && \
  python manage.py migrate --noinput && \
  envsubst '$$PORT' < /etc/nginx/nginx.conf.template > /etc/nginx/nginx.conf && \
  exec supervisord -c /etc/supervisor/supervisord.conf \
"]
