import os
import requests
import redis
import psycopg2
import socket
from flask import Flask, render_template

app = Flask(__name__)

# Универсальная функция для подключения к БД
def get_db_connection():
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'postgres-service'),
        database='cryptodb',
        user='postgres',
        password='supersecret',
        connect_timeout=2
    )

def save_to_db(symbol, price):
    """Записывает одну точку в историю"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        # Используем tstamp (проверь имя колонки в своей БД)
        cur.execute("INSERT INTO history (symbol, price) VALUES (%s, %s)", (symbol, str(price)))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"!!! ОШИБКА ЗАПИСИ: {e}")

@app.route('/')
def index():
    print("--- Запрос на главную страницу ---")
    symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
    results = {}
    
    # 1. Работа с Redis (Кэш)
    r = redis.Redis(host=os.getenv('REDIS_HOST', 'redis-service'), port=6379, decode_responses=True)

    for symbol in symbols:
        price = r.get(symbol)
        source = "cache"
        if not price:
            try:
                res = requests.get(f'https://api.binance.com/api/v3/ticker/price?symbol={symbol}', timeout=5)
                price = res.json()['price']
                r.set(symbol, price, ex=60)
                source = "api"
                # Пишем в базу только свежие данные из API
                save_to_db(symbol, price)
            except Exception as e:
                print(f"Ошибка API для {symbol}: {e}")
                price = "0.0"
        
        results[symbol] = {"price": price, "source": source}

    # 2. Получение данных для ТАБЛИЦЫ и ГРАФИКА
    history_table = []
    prices_graph = []
    times_graph = []
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Данные для таблицы (последние 10 записей всех монет)
        cur.execute("SELECT symbol, price, tstamp FROM history ORDER BY tstamp DESC LIMIT 10;")
        history_table = cur.fetchall()
        
        # Данные для графика (только BTCUSDT, последние 20 точек)
        cur.execute("SELECT price, tstamp FROM history WHERE symbol='BTCUSDT' ORDER BY tstamp DESC LIMIT 20;")
        rows = cur.fetchall()
        
        # Разворачиваем данные, чтобы время на графике шло слева направо
        rows.reverse()
        
        prices_graph = [float(row[0]) for row in rows]
        times_graph = [row[1].strftime('%H:%M:%S') for row in rows]
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"!!! ОШИБКА ЧТЕНИЯ БД ДЛЯ ФРОНТЕНДА: {e}")

    # Возвращаем ВСЕ данные в один шаблон
    return render_template('index.html', 
                           data=results, 
                           history=history_table, 
                           prices=prices_graph, 
                           times=times_graph,
                           host=socket.gethostname())

@app.route('/health')
def health():
    """Проверка для Liveness/Readiness проб Kubernetes"""
    try:
        conn = get_db_connection()
        conn.close()
        return "OK", 200
    except Exception as e:
        return f"Database unreachable: {e}", 500

if __name__ == '__main__':
    # Включаем debug=True только для тестов, в K8s лучше оставить без него
    app.run(host='0.0.0.0', port=5000)