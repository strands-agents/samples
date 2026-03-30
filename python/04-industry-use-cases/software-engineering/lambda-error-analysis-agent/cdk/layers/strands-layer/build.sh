#!/bin/bash

# Build script for Strands Lambda Layer using Docker for Linux compatibility
set -e

echo "Building Strands Lambda Layer using Docker..."

# Clean up any existing python directory
echo "Cleaning up existing python directory..."
rm -rf python/
mkdir -p python/

# Build using Lambda Python base image for Linux x86_64 compatibility
docker run --rm \
    --platform linux/amd64 \
    -v $(pwd):/var/task \
    -w /var/task \
    --entrypoint="" \
    public.ecr.aws/lambda/python:3.12 \
    pip install --target python/ strands-agents strands-agents-tools

echo "Checking layer size..."
du -sh python/
echo "Layer build complete!"