#!/bin/bash
# clean up opensearch serverless resources
echo "Removing Opensearch Serverless resources ..."
python prereqs/opensearch.py --mode delete