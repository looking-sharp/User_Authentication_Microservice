FROM python:3.9-slim-buster
WORKDIR /Authentication_Microservice
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "-u", "auth_app.py"]