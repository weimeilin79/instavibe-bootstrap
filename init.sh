#!/bin/bash

# --- Function for error handling ---
handle_error() {
  echo "Error: $1"
  exit 1
}

# --- Part 1: Set Google Cloud Project ID ---
PROJECT_FILE="$HOME/project_id.txt"
echo "--- Setting Google Cloud Project ID File ---"

read -p "Please enter your Google Cloud project ID: " user_project_id

if [[ -z "$user_project_id" ]]; then
  handle_error "No project ID was entered."
fi

echo "You entered: $user_project_id"
echo "$user_project_id" > "$PROJECT_FILE"

if [[ $? -ne 0 ]]; then
  handle_error "Failed saving your project ID: $user_project_id."
fi
echo "Successfully saved project ID."


# --- Part 2: Clone Repository and Build Docker Image ---
echo
echo "--- Preparing Docker Environment ---"
REPO_URL="https://github.com/weimeilin79/a2a-inspector.git"
REPO_DIR="a2a-inspector"
IMAGE_NAME="a2a-inspector"

# Check if git and docker are installed
if ! command -v git &> /dev/null; then
  handle_error "git is not installed. Please install git to continue."
fi
if ! command -v docker &> /dev/null; then
  handle_error "Docker is not installed or the Docker daemon is not running. Please install and start Docker."
fi

# Navigate to the home directory to perform the clone
echo "Changing to home directory: $HOME"
cd "$HOME" || handle_error "Could not change to home directory."

# Remove the directory if it already exists to ensure a fresh clone
if [[ -d "$REPO_DIR" ]]; then
  echo "Directory '$REPO_DIR' already exists. Removing it for a fresh clone."
  rm -rf "$REPO_DIR"
fi

echo "Cloning repository: $REPO_URL"
git clone "$REPO_URL"
if [[ $? -ne 0 ]]; then
  handle_error "Failed to clone the repository."
fi

# Navigate into the newly cloned repository directory
cd "$REPO_DIR" || handle_error "Could not enter the repository directory '$REPO_DIR'."
echo "Successfully entered directory: $(pwd)"
echo

# --- Part 3: Build and Run Docker Container ---
echo "--- Building Docker image '$IMAGE_NAME' ---"
# The '.' means use the Dockerfile in the current directory
docker build -t "$IMAGE_NAME" .
if [[ $? -ne 0 ]]; then
  handle_error "Docker image build failed."
fi
echo "Docker image built successfully."
echo

echo "--- Running Docker container ---"
# Stop and remove any existing container with the same name to avoid conflicts
if [ "$(docker ps -aq -f name=$IMAGE_NAME)" ]; then
    echo "Stopping and removing existing container named '$IMAGE_NAME'..."
    docker stop "$IMAGE_NAME"
    docker rm "$IMAGE_NAME"
fi

# Run the new container
# -d: Run in detached mode (in the background)
# -p 8081:8080: Map host (VM) port 8081 to container port 8080
# --name: Give the container a predictable name
echo "Starting container and mapping port 8081 (VM) to 8080 (container)."
docker run -d -p 8081:8080 --name "$IMAGE_NAME" "$IMAGE_NAME"
if [[ $? -ne 0 ]]; then
  handle_error "Failed to run the Docker container."
fi

echo "Container '$IMAGE_NAME' started successfully."
echo "You can access the application on this machine at: http://localhost:8081"
echo

echo "--- Setup complete ---"
exit 0