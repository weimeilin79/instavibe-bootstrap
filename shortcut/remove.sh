#!/bin/bash
#
# This script completely tears down the InstaVibe workshop environment.
# It is designed to be idempotent, meaning it will not fail if a resource
# has already been deleted.
#
# WARNING: This operation is destructive and cannot be undone.
#

# Stop the script if any command fails (unless handled with '|| true')
set -e

# --- User-configurable variables ---
REPO_DIR_NAME="instavibe-bootstrap"

# --- Color Codes for Logging ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# --- Safety First: User Confirmation ---
echo -e "${RED}WARNING: This script will permanently delete all InstaVibe resources."
echo -e "${YELLOW}This includes Cloud resources, local files, and IAM role bindings.${NC}"
echo ""
read -p "Are you sure you want to continue? (y/n) " -n 1 -r
echo # Move to a new line
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Operation cancelled."
    exit 1
fi

# --- Step 1: Source Environment Variables ---
echo -e "\n${GREEN}---> Sourcing environment variables...${NC}"
ENV_FILE=~/$REPO_DIR_NAME/set_env.sh
if [ -f "$ENV_FILE" ]; then
    # shellcheck source=/dev/null
    . "$ENV_FILE"
    echo "Environment variables sourced from $ENV_FILE"
else
    echo -e "${YELLOW}Warning: Environment file not found at $ENV_FILE.${NC}"
    echo "The script will attempt to continue, but may fail if variables like PROJECT_ID are not set."
fi

# --- Step 2: Delete Agent Engine ---
echo -e "\n${GREEN}---> Deleting Vertex AI Agent Engine...${NC}"
UTILS_DIR=~/$REPO_DIR_NAME/utils
if [ -d "$UTILS_DIR" ]; then
    cd "$UTILS_DIR"
    # shellcheck source=/dev/null
    source ~/$REPO_DIR_NAME/env/bin/activate
    export ORCHESTRATE_AGENT_ID=$(cat ~/$REPO_DIR_NAME/instavibe/temp_endpoint.txt)
    echo "Attempting to delete Agent Engine with ID: ${ORCHESTRATE_AGENT_ID}"
    
    # Run the Python script but continue even if it fails (e.g., if the agent is already deleted)
    python remote_delete.py || true
    
    deactivate
    cd ~ # Return to home directory for safety
    echo "Agent Engine deletion command executed."
else
    echo -e "${YELLOW}Utils directory not found. Skipping Agent Engine deletion.${NC}"
fi


# --- Step 3: Delete Cloud Run Services ---
echo -e "\n${GREEN}---> Deleting Cloud Run services...${NC}"
gcloud run services delete instavibe --platform=managed --region="${REGION}" --project="${PROJECT_ID}" --quiet || true
gcloud run services delete mcp-tool-server --platform=managed --region="${REGION}" --project="${PROJECT_ID}" --quiet || true
gcloud run services delete planner-agent --platform=managed --region="${REGION}" --project="${PROJECT_ID}" --quiet || true
gcloud run services delete platform-mcp-client --platform=managed --region="${REGION}" --project="${PROJECT_ID}" --quiet || true
gcloud run services delete social-agent --platform=managed --region="${REGION}" --project="${PROJECT_ID}" --quiet || true
echo "Cloud Run services deletion commands executed."

# --- Step 4: Stop and Remove the A2A Inspector Docker Container ---
echo -e "\n${GREEN}---> Removing a2a-inspector Docker container...${NC}"
docker rm --force a2a-inspector || true
echo "Docker container removal command executed."

# --- Step 5: Delete Spanner Instance ---
echo -e "\n${GREEN}---> Deleting Spanner instance: ${SPANNER_INSTANCE_ID}...${NC}"
gcloud spanner instances delete "${SPANNER_INSTANCE_ID}" --project="${PROJECT_ID}" --quiet || true
echo "Spanner instance deletion command executed."

# --- Step 6: Delete Artifact Registry Repository ---
echo -e "\n${GREEN}---> Deleting Artifact Registry repository: ${REPO_NAME}...${NC}"
gcloud artifacts repositories delete "${REPO_NAME}" --location="${REGION}" --project="${PROJECT_ID}" --quiet || true
echo "Artifact Registry repository deletion command executed."

# --- Step 7: Remove Roles from Service Account ---
echo -e "\n${GREEN}---> Removing roles from service account: $SERVICE_ACCOUNT_NAME...${NC}"
if [ -z "$SERVICE_ACCOUNT_NAME" ] || [ -z "$PROJECT_ID" ]; then
    echo -e "${YELLOW}Warning: SERVICE_ACCOUNT_NAME or PROJECT_ID is not set. Skipping IAM role removal.${NC}"
else
    ROLES_TO_REMOVE=(
      "roles/spanner.admin"
      "roles/spanner.databaseUser"
      "roles/artifactregistry.admin"
      "roles/cloudbuild.builds.editor"
      "roles/run.admin"
      "roles/iam.serviceAccountUser"
      "roles/aiplatform.user"
      "roles/logging.logWriter"
      "roles/logging.viewer"
    )

    for role in "${ROLES_TO_REMOVE[@]}"; do
      echo "Removing ${role}..."
      gcloud projects remove-iam-policy-binding "$PROJECT_ID" \
        --member="serviceAccount:$SERVICE_ACCOUNT_NAME" \
        --role="$role" --condition=None --quiet || true
    done
    echo "IAM role removal commands executed."
fi

# --- Step 8: Delete Local Workshop Files ---
echo -e "\n${GREEN}---> Removing local workshop directories and files...${NC}"
rm -rf ~/a2a-inspector
rm -f ~/mapkey.txt
rm -f ~/project_id.txt
echo "Local directories and files removed."


echo -e "\n${GREEN}✅ InstaVibe teardown script finished.${NC}"
echo "Note: Some Google Cloud resources may take a few minutes to be fully de-provisioned."


