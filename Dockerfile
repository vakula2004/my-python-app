FROM python:3.9-slim
WORKDIR /app
# Устанавливаем Flask и экспортер метрик
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "app.py"]
