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

@app.route('/health')
def health():
    """Проверка для Liveness/Readiness проб Kubernetes"""
    try:
        conn = get_db_connection()
        conn.close()
        return "OK", 200
    except Exception as e:
        return f"Database unreachable: {e}", 500
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

    # 2. Получение данных для ТАБЛИЦЫ и ГРАФИКОВ
    history_table = []
    graph_data = {
        'BTCUSDT': {'prices': [], 'times': []},
        'ETHUSDT': {'prices': [], 'times': []},
        'BNBUSDT': {'prices': [], 'times': []}
    }
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Данные для таблицы (последние 10 записей)
        cur.execute("SELECT symbol, price, tstamp FROM history ORDER BY tstamp DESC LIMIT 10;")
        history_table = cur.fetchall()
        
        # Данные для графиков (берем последние 60 записей, чтобы хватило на все 3 валюты)
        cur.execute("""
            SELECT symbol, price, tstamp FROM (
                SELECT symbol, price, tstamp, 
                ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY tstamp DESC) as rn
                FROM history
                WHERE symbol IN ('BTCUSDT', 'ETHUSDT', 'BNBUSDT')
            ) t WHERE rn <= 20 ORDER BY tstamp ASC;
        """)
        
        rows = cur.fetchall()
        for row in rows:
            sym = row[0]
            if sym in graph_data:
                graph_data[sym]['prices'].append(float(row[1]))
                graph_data[sym]['times'].append(row[2].strftime('%H:%M:%S'))
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"!!! ОШИБКА БАЗЫ: {e}")

    return render_template('index.html', 
                           data=results, 
                           history=history_table, 
                           graph_json=graph_data, # Передаем один объект со всеми данными
                           host=socket.gethostname())


if __name__ == '__main__':
    # Включаем debug=True только для тестов, в K8s лучше оставить без него
    app.run(host='0.0.0.0', port=5000)