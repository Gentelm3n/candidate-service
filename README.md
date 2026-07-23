Быстрый старт

Требования

- Docker & Docker Compose
- Make (опционально)

Запуск

bash
# Клонировать репозиторий
git clone <your-repo-url>
cd candidate-service

# Запустить сервис
docker compose up --build
Сервис будет доступен по адресу: http://localhost:8080

Проверка работоспособности
bash
# Health check
curl http://localhost:8080/health

Примеры запросов
Создание операции
bash
curl -X POST http://localhost:8080/operations \
  -H "Content-Type: application/json" \
  -d '{
    "operationId": "order-123",
    "amount": "1000.50",
    "currency": "RUB",
    "description": "Оплата заказа"
  }'
Ответ: 201 Created

json
{
  "operationId": "order-123",
  "amount": "1000.50",
  "currency": "RUB",
  "description": "Оплата заказа",
  "status": "CREATED",
  "providerPaymentId": null,
  "createdAt": "2026-07-23T12:00:00Z",
  "updatedAt": "2026-07-23T12:00:00Z"
}

Отправка на оплату
bash
curl -X POST http://localhost:8080/operations/order-123/submit
Ответ: 202 Accepted (первый запрос) или 200 OK (повторный)

Получение статуса
bash
curl http://localhost:8080/operations/order-123

Получение истории
bash
curl http://localhost:8080/operations/order-123/events

Имитация callback (для тестирования)
bash
curl -X POST http://localhost:8080/receipts \
  -H "Content-Type: application/json" \
  -d '{
    "providerPaymentId": "pay-abc-123",
    "operationId": "order-123",
    "result": "COMPLETED",
    "message": "Payment successful",
    "occurredAt": "2026-07-23T12:05:00Z"
  }'

Полный сценарий
bash
#!/bin/bash

# 1. Создаём операцию
curl -X POST http://localhost:8080/operations \
  -H "Content-Type: application/json" \
  -d '{"operationId":"test-full-001","amount":"500.00","currency":"RUB","description":"Full test"}'

# 2. Отправляем на оплату
curl -X POST http://localhost:8080/operations/test-full-001/submit

# 3. Ждём обработки (воркер отправит запрос провайдеру)
sleep 2

# 4. Имитируем callback
curl -X POST http://localhost:8080/receipts \
  -H "Content-Type: application/json" \
  -d '{
    "providerPaymentId": "pay-test-001",
    "operationId": "test-full-001",
    "result": "COMPLETED",
    "message": "OK",
    "occurredAt": "2026-07-23T12:00:00Z"
  }'

# 5. Проверяем статус
curl http://localhost:8080/operations/test-full-001

# 6. Проверяем историю
curl http://localhost:8080/operations/test-full-001/events
