FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
COPY ../../a2a_common-0.1.0-py3-none-any.whl .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir a2a_common-0.1.0-py3-none-any.whl
COPY . .
EXPOSE 10006
CMD ["python", "a2a_server.py"]
