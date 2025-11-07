FROM python:3.9-slim

# Установите редактор при сборке
RUN apt-get update && apt-get install -y nano

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Переменная для автоматической перезагрузки Flask.
ENV FLASK_RUN_RELOAD=true
# Не необходима. Если изменить в контейнере, дублируется в хост и наооборот.

# Создаем переменную окружения для порта (по умолчанию)
ENV PORT=8080

# Открываем порт (используем переменную)
EXPOSE $PORT

# CMD ["исполняемый_файл", "параметр1", "параметр2"]
CMD ["python", "server.py"]