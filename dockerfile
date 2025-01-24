# Используем официальный Python образ
FROM python:3.9-slim

# Устанавливаем зависимости для работы с Selenium и Chromium
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем необходимые Python пакеты
COPY requirements.txt .
RUN pip install -r requirements.txt

# Копируем весь проект в контейнер
COPY . /app
WORKDIR /app

# Указываем переменную окружения для Chrome
ENV CHROME_BIN=/usr/bin/chromium

# Команда для старта бота
CMD ["python", "bot.py"]
