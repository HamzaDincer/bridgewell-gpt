#!/bin/bash

# Exit on error
set -e

# Configuration
DOCKER_USERNAME="hamzadincer"  # Replace with your Docker Hub username
IMAGE_NAME="bridgewell-gpt"
IMAGE_TAG="latest"

# Check if Docker username is provided
if [ -z "$DOCKER_USERNAME" ]; then
    echo "Please set your Docker Hub username in the script"
    exit 1
fi

# Full image name
FULL_IMAGE_NAME="$DOCKER_USERNAME/$IMAGE_NAME:$IMAGE_TAG"

# Ensure we're logged in to Docker Hub
echo "Please ensure you're logged in to Docker Hub using 'docker login'"

# Build the image for ARM64
echo "Building Docker image for ARM64..."
docker buildx create --use
docker buildx build --platform linux/arm64 \
    --tag "$FULL_IMAGE_NAME" \
    --push \
    -f Dockerfile .

echo "Image built and pushed successfully!"
echo "You can pull the image using: docker pull $FULL_IMAGE_NAME" 