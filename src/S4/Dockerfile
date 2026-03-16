FROM python:3.11-slim

WORKDIR /app

COPY src/S4/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src /app/src
COPY models /app/models

RUN mkdir -p /app/data/raw
COPY data/raw/bootstrap-static.json /app/data/raw/

ENV PYTHONPATH=/app/src

CMD ["uvicorn", "S4.api:app", "--host", "0.0.0.0", "--port", "8000"]