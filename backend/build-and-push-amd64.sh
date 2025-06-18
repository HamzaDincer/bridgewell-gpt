#!/bin/bash

# Exit on error
set -e

# Configuration
DOCKER_USERNAME="hamzadincer"  # Your Docker Hub username
IMAGE_NAME="bridgewell-gpt"
IMAGE_TAG="0.0.7"

# Full image name
FULL_IMAGE_NAME="$DOCKER_USERNAME/$IMAGE_NAME:$IMAGE_TAG"

# Ensure we're logged in to Docker Hub
echo "Please ensure you're logged in to Docker Hub using 'docker login'"

# Build the image for AMD64
echo "Building Docker image for AMD64..."
docker buildx create --use
docker buildx build --platform linux/amd64 \
    --tag "$FULL_IMAGE_NAME" \
    --push \
    -f Dockerfile.amd64 .

echo "Image built and pushed successfully!"
echo "You can pull the image using: docker pull $FULL_IMAGE_NAME" 