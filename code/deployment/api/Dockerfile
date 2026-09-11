FROM python:3.13-slim AS dependencies
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 MODEL_DIR=/app/models
WORKDIR /app
COPY requirements-model.txt ./
COPY code/deployment/api/requirements.txt ./requirements-api.txt
RUN pip install --no-cache-dir -r requirements-api.txt && useradd --create-home appuser
FROM dependencies AS runtime
COPY code/deployment/api/main.py ./main.py
COPY models/model.joblib models/metadata.json ./models/
USER appuser
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
