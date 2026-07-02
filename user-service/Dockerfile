FROM python:3.12-slim

LABEL maintainer=naveenshijo@gmail.com
LABEL application=user-service
LABEL version=1.17
LABEL description="Fastapi based user microservice"

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 

WORKDIR /user-home/
COPY requirements.txt .

# RUN apt-get update && apt-get install -y gcc build-essential && rm -rf /var/lib/apt/lists/*
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "users:app", "--host", "0.0.0.0", "--port", "8000"]