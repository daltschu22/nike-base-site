FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 APP_ENV=production DATABASE_PATH=/data/nike_sites.db PORT=8000
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && useradd --uid 10001 --create-home nike \
    && mkdir /data && chown nike:nike /data
COPY --chown=nike:nike app ./app
COPY --chown=nike:nike main.py config.py import_sites.py ./
USER nike
EXPOSE 8000
HEALTHCHECK --interval=30s --start-period=60s --timeout=5s CMD python -c "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:' + os.environ.get('PORT', '8000') + '/healthz', timeout=3)"
CMD ["python", "main.py"]
