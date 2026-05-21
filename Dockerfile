FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod -R a+rX /app

ENV HOST=0.0.0.0
ENV PORT=8000
ENV DATA_DIR=/app/data

EXPOSE 8000

CMD ["python", "server.py"]
