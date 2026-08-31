FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# collectstatic only needs *a* valid SECRET_KEY to import settings — it never
# needs the real one. The real SECRET_KEY is injected at runtime via env and
# is never baked into the image.
RUN SECRET_KEY=build-time-placeholder DEBUG=False python manage.py collectstatic --noinput

RUN useradd --create-home --uid 1000 appuser \
    && mkdir -p /data \
    && chown -R appuser:appuser /app /data
USER appuser

EXPOSE 8000

CMD ["sh", "-c", "python manage.py migrate --noinput && gunicorn django_shorty.wsgi:application --bind 0.0.0.0:8000 --workers 3"]
