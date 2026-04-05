FROM python:3.12-slim

WORKDIR /app

# Install dependencies using batch-specific requirements (no mangum/cryptography/resend)
COPY batch/requirements.txt ./batch/requirements.txt
RUN pip install --no-cache-dir -r batch/requirements.txt

# Copy the full Django app so worker.py can import models
COPY . .

# worker.py lives at batch/worker.py, run as a module from /app
ENTRYPOINT ["python", "batch/worker.py"]
