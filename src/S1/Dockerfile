FROM python:3.11-slim

WORKDIR /app

# requirements install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# projekt copy
COPY . .

# from import path
ENV PYTHONPATH=/app/src

CMD ["python", "src/S1/main.py"]