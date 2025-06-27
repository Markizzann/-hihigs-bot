#     Dockerfile используется для создания Docker-образа, обеспечивает воспроизводимое окружение для запуска, устанавливая зависимости и копируя код, а затем запуская основной скрипт
FROM python:3.13-slim
WORKDIR /app
COPY ../requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY .. .
CMD ["python3", "-u", "script/main.py"]
