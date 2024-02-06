FROM --platform=linux/amd64 python:3.11-slim-bookworm

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip3 install -U -r requirements.txt

COPY . /app/
RUN chmod +x /app/main.py

CMD ["python3", "/app/main.py"]