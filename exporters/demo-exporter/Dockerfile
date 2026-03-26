FROM python:3.12-slim

LABEL maintainer="Shivaji Chaprana <shivajichaprana97@gmail.com>"

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt 2>/dev/null || true

COPY exporter.py .

USER nobody

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["python", "-u", "exporter.py"]
