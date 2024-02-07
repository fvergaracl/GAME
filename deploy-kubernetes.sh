#!/bin/bash

# Assuming this script is located in the "kubernetes" directory
# and the YAML files are also within this directory or its subdirectories.

# Change directory to the location of the script
cd "$(dirname "$0")"

# Source the .env file to load environment variables
if [ -f ".env" ]; then
    export $(cat .env | sed 's/#.*//g' | xargs)
fi

# Define the namespace where resources will be deployed
NAMESPACE=${GAMIFICATIONENGINE_NAMESPACE}

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to apply a YAML file and display colored messages
apply_yaml() {
    FILE=$1
    VERBOSE=$2
    TEMP_FILE="temp-$(basename $FILE)"

    # Use envsubst to substitute environment variable values in the YAML file
    envsubst < $FILE > $TEMP_FILE

    if [ "$VERBOSE" = "--verbose" ]; then
        echo -e "${YELLOW}Executing command: kubectl --namespace $NAMESPACE apply -f $TEMP_FILE${NC}"
    fi
    kubectl --namespace $NAMESPACE apply -f $TEMP_FILE

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}[+] Success: The resource $TEMP_FILE has been successfully applied to the namespace $NAMESPACE.${NC}"
    else
        echo -e "${RED}[-] Error: Failed to apply the resource $TEMP_FILE to the namespace $NAMESPACE.${NC}"
    fi

    # Remove the temporary file after applying
    rm $TEMP_FILE
}

# List of YAML files to apply
FILES=(
    "kubernetes/configmaps/env-prod-configmap.yaml"
    "kubernetes/volumen/postgres-data-persistentvolumeclaim.yaml"
    "kubernetes/services/gamificationengine-service.yaml"
    "kubernetes/services/postgres-service.yaml"
    "kubernetes/deployments/gamificationengine-deployment.yaml"
    "kubernetes/deployments/postgres-deployment.yaml"
    "kubernetes/ingresses/ingress.yaml"
)

# Apply each YAML file
for FILE in "${FILES[@]}"; do
    apply_yaml $FILE $1
done

echo -e "${BLUE}[*] Info: Process completed.${NC}"
