#!/bin/bash

# NOTEBOOK_FILE='awsStrands_mcp-singleAgent_singleTurn.ipynb'
# NOTEBOOK_FILE='awsStrands-multiAgent_multiTurn.ipynb'
# NOTEBOOK_FILE='awsStrands-multiAgent_singleTurn.ipynb'
NOTEBOOK_FILE='awsStrands-singleAgent_multiTurn.ipynb'
# NOTEBOOK_FILE='awsStrands-singleAgent_singleTurn.ipynb'

# Check if the notebook file exists
if [ ! -f "$NOTEBOOK_FILE" ]; then
    echo "Error: Notebook file '$NOTEBOOK_FILE' not found."
    exit 1
fi

# Extract the filename without extension
FILENAME=$(basename "$NOTEBOOK_FILE" .ipynb)
PYTHON_FILE="${FILENAME}.py"

echo "Converting $NOTEBOOK_FILE to Python..."
# Convert notebook to Python
jupyter nbconvert --to script "$NOTEBOOK_FILE"

if [ $? -ne 0 ]; then
    echo "Error: Failed to convert notebook to Python."
    exit 1
fi

echo "Running $PYTHON_FILE..."
# Run the Python file
../../../venv/bin/python "$PYTHON_FILE"

echo "Cleaning up..."
# Remove the generated Python file
# rm "$PYTHON_FILE"