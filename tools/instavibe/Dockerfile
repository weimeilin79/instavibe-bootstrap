# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# --- Dependency Installation ---
COPY requirements.txt /app/requirements.txt 
RUN pip install --no-cache-dir -r requirements.txt

# --- Application Code ---
COPY . /app

# --- Environment ---
ENV PYTHONPATH=/app

# Make port 8080 available to the world outside this container
# Cloud Run uses the PORT env var, but EXPOSE is good practice.
EXPOSE 8080

# --- Run the application ---
CMD ["python", "mcp_server.py"]