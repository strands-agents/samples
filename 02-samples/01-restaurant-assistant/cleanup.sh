# clean up knowledge base
echo "Removing knowledge base resources ..."
python prereqs/knowledge_base.py --mode delete

# clean up dynamodb
echo "Removing DynamoDB resources..."
python prereqs/dynamodb.py --mode delete



