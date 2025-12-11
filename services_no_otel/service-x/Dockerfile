FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py ./app.py
COPY start.sh ./start.sh
RUN chmod +x ./start.sh

ENV SERVICE_NAME=service-x \
    SERVICE_Y_URL=http://service-y:8000/process

EXPOSE 8000

CMD ["./start.sh"]
