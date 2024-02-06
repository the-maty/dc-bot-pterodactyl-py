FROM --platform=linux/amd64 python:3.11-slim-bookworm as build
FROM --platform=linux/arm64 python:3.11-slim-bookworm as build

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip3 install -U -r requirements.txt

COPY . .

CMD ["python3", "main.py"]