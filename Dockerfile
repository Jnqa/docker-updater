FROM python:3.10.5-slim-buster
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
COPY requirements.txt .
RUN python3 -m pip install -r requirements.txt
RUN apt-get update
RUN apt install -y sshpass

WORKDIR /app
COPY . /app

RUN useradd appuser && chown -R appuser /app
USER appuser

CMD ["python3", "main.py"]