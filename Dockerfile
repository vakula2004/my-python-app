# Стейдж 1: Сборка зависимостей
FROM python:3.9-slim as builder

WORKDIR /app

# Устанавливаем системные зависимости для компиляции psycopg2
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Копируем только список зависимостей для кэширования слоев
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Стейдж 2: Финальный образ
FROM python:3.9-slim

WORKDIR /app

# Для работы psycopg2 в рантайме нужна только libpq
RUN apt-get update && apt-get install -y \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Копируем установленные пакеты из первого стейджа
COPY --from=builder /root/.local /root/.local
COPY . .

# Обновляем PATH, чтобы Python видел пакеты
ENV PATH=/root/.local/bin:$PATH

EXPOSE 5000

CMD ["python", "app.py"]