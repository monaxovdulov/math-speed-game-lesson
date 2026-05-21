FROM python:3.12-slim

WORKDIR /app

COPY . .

RUN chmod -R a+rX /app

ENV HOST=0.0.0.0
ENV PORT=8000
ENV DATA_DIR=/app/data

EXPOSE 8000

CMD ["python", "server.py"]
