FROM python:3.11-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . . # Copies tools.py and mcp_server.py

EXPOSE 8081 # As defined by BQ_MCP_SERVER_PORT

# Environment variables can be set here or passed during runtime
# ENV BQ_MCP_SERVER_HOST="0.0.0.0"
# ENV BQ_MCP_SERVER_PORT="8081"

CMD ["python", "mcp_server.py"]
