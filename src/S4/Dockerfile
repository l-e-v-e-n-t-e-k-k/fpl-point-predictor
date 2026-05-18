FROM python:3.11-slim

WORKDIR /app

COPY src/S4/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src /app/src

ENV PYTHONPATH=/app/src
ENV MODEL_BASE_DIR=/models
ENV MODEL_POLL_SECONDS=10

CMD ["uvicorn", "S4.api:app", "--host", "0.0.0.0", "--port", "8000"]
