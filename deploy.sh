#!/bin/bash

# Deploy to Render using API
RENDER_API_KEY=$API_KEY

# Function to deploy a service by name
deploy_service() {
    local service_name=$1
    local service_id=$(curl -s -H "Authorization: Bearer $RENDER_API_KEY" https://api.render.com/v1/services | jq -r ".[] | select(.name == \"$service_name\") | .id")
    if [ -n "$service_id" ]; then
        echo "Deploying $service_name (ID: $service_id)"
        curl -X POST https://api.render.com/v1/services/$service_id/deploys \
            -H "Authorization: Bearer $RENDER_API_KEY" \
            -H "Content-Type: application/json" \
            -d '{}'
    else
        echo "Service $service_name not found"
    fi
}

# Deploy backend and frontend
deploy_service "roboto-sai-backend"
deploy_service "roboto-sai-frontend"