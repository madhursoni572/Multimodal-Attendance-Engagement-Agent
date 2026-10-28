FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg libsndfile1 && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV DATA_DIR=/tmp/data NUMBA_CACHE_DIR=/tmp/numba
EXPOSE 8000 8501
# One worker: job state lives in memory.
CMD uvicorn main:app --app-dir backend --host 0.0.0.0 --port ${PORT:-8000}
