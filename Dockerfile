FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir gunicorn

COPY . .

RUN mkdir -p data

EXPOSE 10000

CMD ["gunicorn", "--bind", "0.0.0.0:10000", "--workers", "1", "--timeout", "60", "app:app"]
