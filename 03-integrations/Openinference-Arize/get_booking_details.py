from strands import tool
import boto3 

@tool
def get_booking_details(booking_id:str, restaurant_name:str) -> dict:
    """Get the relevant details for booking_id in restaurant_name
    Args:
        booking_id: the id of the reservation
        restaurant_name: name of the restaurant handling the reservation

    Returns:
        booking_details: the details of the booking in JSON format
    """
    kb_name = 'restaurant-assistant'
    dynamodb = boto3.resource('dynamodb')
    smm_client = boto3.client('ssm')
    table_name = smm_client.get_parameter(
        Name=f'{kb_name}-table-name',
        WithDecryption=False
    )
    table = dynamodb.Table(table_name["Parameter"]["Value"])
    try:
        response = table.get_item(
            Key={
                'booking_id': booking_id, 
                'restaurant_name': restaurant_name
            }
        )
        if 'Item' in response:
            return response['Item']
        else:
            return f'No booking found with ID {booking_id}'
    except Exception as e:
        return str(e)
