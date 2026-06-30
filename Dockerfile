FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY scanner/ /app/scanner/

CMD ["python", "-m", "scanner.pipeline"]
