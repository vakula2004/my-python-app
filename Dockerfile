FROM python:3.9-slim
WORKDIR /app
# Устанавливаем Flask и экспортер метрик
RUN pip install flask prometheus-flask-exporter
COPY . .
EXPOSE 5000
CMD ["python", "app.py"]
