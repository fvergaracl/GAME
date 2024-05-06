#!/bin/bash


cd "$(dirname "$0")"


if [ -f ".env" ]; then
    export $(cat .env | sed 's/#.*//g' | xargs)
fi

NAMESPACE=${GAMIFICATIONENGINE_NAMESPACE}

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

show_help() {
    echo "Usage: $0 [OPTION]"
    echo "Apply Kubernetes YAML files for specific components."
    echo ""
    echo "Options:"
    echo "  --postgres  Apply only the PostgreSQL deployment and its dependencies."
    echo "  --api       Apply only the API deployment and its dependencies."
    echo "  --verbose   Display verbose output."
    echo "  --help      Display this help message."
    echo ""
    echo "Examples:"
    echo "  $0 --postgres        # Apply only the PostgreSQL deployment."
    echo "  $0 --api             # Apply only the API deployment."
    echo "  $0 --api --verbose   # Apply only the API deployment with verbose output."
}

apply_yaml() {
    FILE=$1
    VERBOSE=$2
    TEMP_FILE="temp-$(basename $FILE)"

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

    rm $TEMP_FILE
}

for arg in "$@"; do
    if [ "$arg" = "--help" ]; then
        show_help
        exit 0
    fi
done

POSTGRES_FILES=(
    "kubernetes/volumen/postgres-data-persistentvolumeclaim.yaml"
    "kubernetes/services/postgres-service.yaml"
    "kubernetes/deployments/postgres-deployment.yaml"
)

API_FILES=(
    "kubernetes/configmaps/env-prod-configmap.yaml"
    "kubernetes/services/gamificationengine-service.yaml"
    "kubernetes/deployments/gamificationengine-deployment.yaml"
)

INGRESS=(
    "kubernetes/ingresses/ingress.yaml"

)

if [ "$1" = "--postgres" ]; then
    FILES=("${POSTGRES_FILES[@]}")
elif [ "$1" = "--api" ]; then
    FILES=("${API_FILES[@]}")
elif [ "$1" = "--ingress" ]; then
    FILES=("${INGRESS[@]}")
else
    echo "Invalid option or no option provided. Use --help for usage information."
    exit 1
fi

for FILE in "${FILES[@]}"; do
    apply_yaml $FILE $2 # $2 can be --verbose
done

echo -e "${BLUE}[*] Info: Process completed.${NC}"
