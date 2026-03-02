FROM python:3.9-slim
WORKDIR /app
# Важно: устанавливаем flask
RUN pip install flask 
COPY . .
# Убедись, что файл называется именно app.py
CMD ["python", "app.py"]
