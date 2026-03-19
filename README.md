📈 Crypto-Monitor Pro: K8s Microservices Stack

Полноценное облачное приложение для мониторинга криптовалют с использованием GitOps и Self-healing архитектуры. Развернуто в локальном Kubernetes кластере (Kubespray).
🏗 Архитектура системы

Приложение построено по принципу 3-Tier Architecture:

    Frontend/API: Python Flask (Jinja2 + Bootstrap 5).

    Caching Layer: Redis (хранение текущих курсов, TTL 60с).

    Persistence Layer: PostgreSQL 15 (хранение истории изменений цен).

    Infrastructure: Kubernetes, ArgoCD, Jenkins, Kaniko.

🛠 Технологический стек

    Orchestration: Kubernetes (v1.28+)

    CI/CD: Jenkins (Pipelines), Kaniko (контейнеризация без привилегий), ArgoCD (GitOps).

    Storage: Persistent Volume Claims (PVC) для отказоустойчивости БД.

    Reliability: Liveness & Readiness Probes для автоматического восстановления сервисов.

    Networking: Ingress-nginx, NodePort Services.

🚀 Как это работает (Workflow)

    CI: При пуше в GitHub, Jenkins запускает билд. Kaniko собирает образ и пушит в Docker Hub.

    CD: ArgoCD замечает изменения в манифестах и синхронизирует состояние кластера.

    Logic: Приложение опрашивает Binance API. Если данные есть в Redis, берет оттуда. Если нет — запрашивает API, обновляет кэш и записывает транзакцию в PostgreSQL.

    Health: Kubernetes постоянно опрашивает эндпоинт /health. Если связь с БД потеряна, под автоматически выводится из ротации и перезагружается.

📊 Мониторинг и проверка

Проверка статуса подов и хранилища:
Bash

kubectl get pods -n default
kubectl get pvc postgres-pvc

Просмотр последних записей в БД:
Bash

kubectl exec -it <postgres-pod-name> -- psql -U postgres -d cryptodb -c "SELECT * FROM history LIMIT 10;"

🔧 Установка (Quick Start)

    Склонируйте репозиторий.

    Примените манифесты базы данных: kubectl apply -f k8s/postgres.yaml.

    Примените манифесты кэша: kubectl apply -f k8s/redis.yaml.

    Настройте ArgoCD на папку k8s/ для автоматического деплоя приложения.

Что этот проект демонстрирует (Skills):

    Умение работать с Stateful нагрузками в K8s (PVC/PV).

    Настройка межсервисного взаимодействия (Service Discovery).

    Написание отказоустойчивого кода на Python.

    Автоматизация через GitOps (Source of Truth — Git).