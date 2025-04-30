#!/bin/bash

# Exit on any error
set -e

# Load environment variables if .env exists
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Variables
IMAGE_NAME="telegram-bot"
CONTAINER_NAME="telegram-bot-container"
VM_USER=${YC_VM_USER:-"yc-user"}
VM_IP=${YC_VM_IP}  # Should be set in .env

# Check if VM_IP is set
if [ -z "$VM_IP" ]; then
    echo "Error: YC_VM_IP is not set in .env file"
    exit 1
fi

echo "Deploying to VM at $VM_IP..."

echo "Building Docker image..."
docker build -t $IMAGE_NAME .

echo "Saving Docker image..."
docker save $IMAGE_NAME | gzip > ${IMAGE_NAME}.tar.gz

echo "Copying files to VM..."
scp ${IMAGE_NAME}.tar.gz $VM_USER@$VM_IP:~
scp .env $VM_USER@$VM_IP:~

echo "Loading and running container on VM..."
ssh $VM_USER@$VM_IP << EOF
    # Load Docker image
    docker load < ${IMAGE_NAME}.tar.gz
    
    # Stop and remove existing container if it exists
    docker stop $CONTAINER_NAME || true
    docker rm $CONTAINER_NAME || true
    
    # Run new container
    docker run -d \
        --name $CONTAINER_NAME \
        --restart unless-stopped \
        --network="host" \
        --env-file .env \
        $IMAGE_NAME
        
    # Verify container is running
    if docker ps | grep -q $CONTAINER_NAME; then
        echo "Container started successfully"
    else
        echo "Error: Container failed to start"
        exit 1
    fi
        
    # Cleanup
    rm ${IMAGE_NAME}.tar.gz
EOF

echo "Cleaning up local files..."
rm ${IMAGE_NAME}.tar.gz

echo "Deployment completed successfully!"

# Wait a bit and check logs
echo "Checking container logs..."
ssh $VM_USER@$VM_IP "docker logs $CONTAINER_NAME --tail 50" 