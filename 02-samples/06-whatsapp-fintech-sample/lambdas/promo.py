import boto3
import os

from strands import tool
from boto3.dynamodb.conditions import Key
from datetime import datetime


DEFAULT_LOCALE=os.environ['LOCALE']
dynamodb_resource=boto3.resource('dynamodb')
dynamodb_table=os.getenv('PROMO_TABLE')

translations = {
    "pt_BR": {
        "promo1_platinum": "Anuidade gratuita para o cartão Platinum",
        "promo2_diamond": "Isenção na mensalidade da conta Diamond",
        "promo1_gold": "Cashback de 0,8% para o cartão Gold",
        "promo2_brinde": "Ganhe um brinde especial",
        "promo1_marketplace": "R$20 reais de cashback no marketplace para compras acima de R$100",
        "promo1_seguro": "Seguro celular com desconto de 10%",
        "error_query": "Erro ao consultar a tabela: {table_name}.",
        "error_insert": "Erro ao inserir na tabela: {dynamodb_table}.",
        "error_function": "Erro, função '{function}' não reconhecida"
    },
    "en_US": {
        "promo1_platinum": "Free annual fee for the Platinum card",
        "promo2_diamond": "Waiver of the monthly fee for the Diamond account",
        "promo1_gold": "0.8% cashback for the Gold card",
        "promo2_brinde": "Receive a special gift",
        "promo1_marketplace": "$20 cashback in the marketplace for purchases over $100",
        "promo1_seguro": "10% discount on cell phone insurance",
        "error_query": "Error querying the table: {table_name}.",
        "error_insert": "Error inserting into the table: {dynamodb_table}.",
        "error_function": "Error, function '{function}' not recognized"
    }
}

def get_translation(key, **kwargs):
    return translations[DEFAULT_LOCALE][key].format(**kwargs)

def read_dynamodb(table_name: str, pk_value: str):
    try:
        table = dynamodb_resource.Table(table_name)
        # Create expression
        key_expression = Key('week_day').eq(pk_value)
        query_data = table.query(KeyConditionExpression=key_expression)
        return query_data['Items']
    except Exception as err:
        print(f'Error querying table: {table_name}.')
        print(f'Exception: {err}')

def load_data(week_day):
    try:
        promotions = [
            {"week_day": 0, "promo1": get_translation("promo1_platinum"), "promo2": get_translation("promo2_diamond")},
            {"week_day": 1, "promo1": get_translation("promo1_gold"), "promo2": get_translation("promo2_brinde")},
            {"week_day": 2, "promo1": get_translation("promo1_platinum"), "promo2": get_translation("promo2_brinde")},
            {"week_day": 3, "promo1": get_translation("promo1_marketplace")},
            {"week_day": 4, "promo1": get_translation("promo1_seguro"), "promo2": get_translation("promo1_platinum")},
            {"week_day": 5, "promo1": get_translation("promo2_brinde")},
            {"week_day": 6, "promo1": get_translation("promo2_diamond"), "promo2": get_translation("promo2_brinde")}
        ]
        
        table = dynamodb_resource.Table(dynamodb_table)

        for promo in promotions:
            response = table.put_item(Item=promo)
    except Exception as err:
        print(f'Error inserting on table: {dynamodb_table}.')
        print(f'Exception: {err}')

@tool
def get_promotions() -> str:
    """
        Get promotions based on Ptyhon day of the week.

        Invoke get_day_of_week() to discover current day of the week.
    """
    #print(f'env-var table: {dynamodb_table}')
    # Day of the week
    week_day = get_day_of_week()
    
    response = read_dynamodb(dynamodb_table, week_day)
    if not response:
        load_data(week_day)
        response = read_dynamodb(dynamodb_table, week_day)
    return response

@tool
def get_day_of_week() -> str:
    """
        Get day of the week based on Python day of the week:

        0 = Monday
        1 = Tuesday
        2 = Wednesday
        3 = Thursday
        4 = Friday
        5 = Saturday
        6 = Sunday
    """
    # Day of the week
    week_day = datetime.today().weekday()
    return week_day