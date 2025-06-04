# Используем официальный образ Python
FROM python:3.12-slim

# Устанавливаем зависимости системы
RUN apt-get update && apt-get install -y \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем Poetry
RUN pip install --no-cache-dir poetry

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы проекта
COPY pyproject.toml poetry.lock ./
COPY . .

# Устанавливаем зависимости через Poetry
RUN poetry config virtualenvs.create false && poetry install --no-root
# Указываем порт для API
EXPOSE 8000

# Команда для запуска приложения
CMD ["uvicorn", "app.main:app", "--reload", "--port=8000", "--host=0.0.0.0"]
