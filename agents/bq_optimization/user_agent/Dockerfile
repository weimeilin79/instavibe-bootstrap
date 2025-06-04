# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Copy the a2a_common wheel from the host path (relative to Dockerfile) to the container
# This path must be relative to the Docker build context (agents/bq_optimization/user_agent/)
COPY ../../a2a_common-0.1.0-py3-none-any.whl .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
# Install the local a2a_common wheel
RUN pip install --no-cache-dir a2a_common-0.1.0-py3-none-any.whl

# Copy the rest of the application code into the container at /app
COPY . .

# Make port available (defined by BQ_USER_AGENT_A2A_PORT, defaults to 10005)
EXPOSE 10005

# Define environment variables if necessary
# ENV BQ_USER_AGENT_A2A_HOST="0.0.0.0"
# ENV BQ_USER_AGENT_A2A_PORT="10005"
# ENV BQ_USER_AGENT_PUBLIC_URL=""
# ENV LENS_AGENT_ADDRESS=""

CMD ["python", "a2a_server.py"]
