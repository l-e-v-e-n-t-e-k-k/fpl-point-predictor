FROM python:3.11-slim

WORKDIR /app

COPY src/S3/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src /app/src

ENV PYTHONPATH=/app/src
ENV MODEL_BASE_DIR=/models

CMD ["python", "src/S3/train_and_evaluate.py"]
