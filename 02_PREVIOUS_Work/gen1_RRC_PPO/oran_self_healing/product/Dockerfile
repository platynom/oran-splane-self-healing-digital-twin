FROM python:3.11-slim
WORKDIR /app
COPY product/requirements.txt /app/product/requirements.txt
RUN pip install --no-cache-dir -r /app/product/requirements.txt
COPY . /app
EXPOSE 8080
# fit artifacts at build time so the service boots ready
RUN python product/pipeline.py train || true
CMD ["uvicorn", "product.governor_service:app", "--host", "0.0.0.0", "--port", "8080"]
