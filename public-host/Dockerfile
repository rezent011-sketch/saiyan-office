FROM python:3.12-slim
WORKDIR /app
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt
COPY backend /app/backend
COPY frontend /app/frontend
COPY scripts /app/scripts
COPY public-host /app/public-host
COPY public-queue /app/public-queue
ENV PORT=8080
ENV PUBLIC_OFFICE_QUEUE=/app/public-queue/queue.json
EXPOSE 8080
CMD ["python3", "/app/public-host/app.py"]
