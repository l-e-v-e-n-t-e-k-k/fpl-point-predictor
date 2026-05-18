FROM python:3.11-slim

WORKDIR /app

COPY src/S2/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src /app/src
COPY data /app/data

ENV PYTHONPATH=/app/src

CMD ["uvicorn", "S2.api:app", "--host", "0.0.0.0", "--port", "8001"]
