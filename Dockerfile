FROM python:3.11-slim
WORKDIR /app
COPY app/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY app /app
ENV JWT_SECRET="SUPER_SECRET_KEY"
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
