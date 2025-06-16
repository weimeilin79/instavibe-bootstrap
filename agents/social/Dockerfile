# /Users/linchr/Desktop/work/datecoach/agents/social/Dockerfile

# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app
RUN pip install --upgrade pip

# --- Dependency Installation ---
# Copy only the requirements file first to leverage Docker cache
COPY ./social/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt


# --- Application Code ---
COPY ./social /app/agents/social

# --- Environment ---
ENV PYTHONPATH=/app/agents 


# Make port 8080 available to the world outside this container
# Cloud Run uses the PORT env var, but EXPOSE is good practice.
EXPOSE 8080

# --- Run the application ---
# Run a2a_server.py when the container launches
# Use the module execution '-m' which works well with the PYTHONPATH setup
CMD ["python", "-m", "social.a2a_server"]