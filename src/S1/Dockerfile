FROM python:3.11-slim

WORKDIR /app

COPY src/S1/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src /app/src

ENV PYTHONPATH=/app/src

CMD ["uvicorn", "S1.api:app", "--host", "0.0.0.0", "--port", "8002"]
