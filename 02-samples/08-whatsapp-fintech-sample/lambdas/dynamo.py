import boto3
import logging
from datetime import datetime
from boto3.dynamodb.conditions import Key


logger = logging.getLogger(__name__)


class DynamoDB:
    def __init__(self) -> None:
        self.client = boto3.resource('dynamodb')

    def save_item_ddb(self, table, item):
        try:
            dynamo_table = self.client.Table(table)
            response = dynamo_table.put_item(Item=item)
            return response
        except Exception as e:
            logger.error("Error saving item to DynamoDB: %s", e)
            raise

    def query(self, table, key, keyvalue, sort_key, sort_value):
        try:
            dynamo_table = self.client.Table(table)
            response = dynamo_table.query(
                KeyConditionExpression=Key(key).eq(keyvalue) & Key(sort_key).eq(sort_value)
            )
            logger.info("Query successful: %s", response)
            return response['Items'], response['Count']
        except Exception as e:
            logger.error("Error querying DynamoDB: %s", e)
            raise

    def query_by_day(self, table, phone_number):
        try:
            dynamo_table = self.client.Table(table)
            current_day = datetime.now().strftime("%Y/%m/%d")
            response = dynamo_table.scan(
                FilterExpression=Key('phone_number').eq(phone_number) & Key('day').eq(current_day)
            )
            logger.info("Query by day successful: %s", response)
            #print("Query by day successful: %s", response)
            return response['Items']
        except Exception as e:
            logger.error("Error querying by day from DynamoDB: %s", e)
            raise

    def insert_user_message(self, table, row):
        try:
            
            #print(f"Row: {row}")
            response = self.save_item_ddb(table, row)
            return response
        except Exception as e:
            logger.error("Error updating message on DynamoDB: %s", e)
            raise

    def query_with_gsi(self, table, index_name, key, keyvalue, sort_key=None, sort_value=None, ascending=True):
        try:
            dynamo_table = self.client.Table(table)
            key_condition = Key(key).eq(keyvalue)
            if sort_key and sort_value:
                key_condition &= Key(sort_key).eq(sort_value)
            
            response = dynamo_table.query(
                IndexName=index_name,  # Nome do índice secundário global
                KeyConditionExpression=key_condition,
                ScanIndexForward=ascending  # Ordenação ascendente ou descendente
            )
            logger.info("Query with GSI successful: %s", response)
            return response['Items'], response['Count']
        except Exception as e:
            logger.error("Error querying DynamoDB with GSI: %s", e)
            raise