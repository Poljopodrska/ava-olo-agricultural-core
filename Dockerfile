FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN python3 -m pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8080
CMD ["python3", "-m", "uvicorn", "api_gateway_minimal:app", "--host", "0.0.0.0", "--port", "8080"]