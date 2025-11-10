FROM python:3.9-slim-buster
WORKDIR /User_Authentication_Microservice
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "auth_app.py"]