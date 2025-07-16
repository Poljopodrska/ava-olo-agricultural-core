FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN python3 -m pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8080
CMD ["python3", "api_gateway_emergency.py"]