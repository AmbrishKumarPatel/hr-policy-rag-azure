# Python ka chhota image
FROM python:3.12-slim

WORKDIR /app

# Pehle sirf requirements, taaki baar-baar install na ho
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Phir code
COPY src/ ./src/
WORKDIR /app/src

EXPOSE 8000
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]