import os
import random
from datetime import datetime, timedelta
from strands import tool


DEFAULT_LOCALE=os.environ['LOCALE']

translations = {
    "pt_BR": {
        "supermarket_purchase": "Compra de supermercado",
        "bill_payment": "Pagamento de conta",
        "service_subscription": "Assinatura de serviço",
        "online_purchase": "Compra online",
        "restaurant_meal": "Refeição em restaurante",
        "payment_scheduled": "Obrigado {name}. Pagamento agendado para {payment_date}.",
        "error_quantity": "Erro: O valor de 'quantity' deve estar entre 1 e 15 dias.",
        "error_function": "Erro, função '{function}' não reconhecida"
    },
    "en_US": {
        "supermarket_purchase": "Supermarket purchase",
        "bill_payment": "Bill payment",
        "service_subscription": "Service subscription",
        "online_purchase": "Online purchase",
        "restaurant_meal": "Restaurant meal",
        "payment_scheduled": "Thank you {name}. Payment scheduled for {payment_date}.",
        "error_quantity": "Error: The value of 'quantity' must be between 1 and 15 days.",
        "error_function": "Error, function '{function}' not recognized"
    }
}


def get_translation(key, **kwargs):
    return translations[DEFAULT_LOCALE][key].format(**kwargs)


@tool
def get_transactions(name: str, quantity: str) -> dict:
    """Get last N transactions from customer credit card bill, being N number of past days

    Args:
        name: The name of the customer
        quantity: Last N days, amount of past days to consider in filter
    """
    invoice = {
        "card_holder": name,
        "card_number": "1234 5678 9012 3456",
        "total_amount": round(random.uniform(100, 5000), 2),
        "due_date": (datetime.today().replace(day=28)).strftime('%Y-%m-%d'),
        "transactions": []
    }

    # description list
    descriptions = [
        get_translation("supermarket_purchase"),
        get_translation("bill_payment"),
        get_translation("service_subscription"),
        get_translation("online_purchase"),
        get_translation("restaurant_meal")
    ]

    # Adding fake transactions
    for _ in range(int(quantity)):  # adding quantity of transactions
        days_ago = random.randint(5, 10)
        transaction_date = (datetime.today() - timedelta(days=days_ago)).strftime('%Y-%m-%d')
        transaction = {
            "date": transaction_date,
            "description": random.choice(descriptions),
            "amount": round(random.uniform(10, 500), 2)
        }
        invoice["transactions"].append(transaction)

    #print(f'Invoice final: {invoice}')
    return invoice


@tool
def put_payment(name: str, quantity: str) -> str:
    """Schedule a payment for a customer

    Args:
        name: The name of the customer
        quantity: Future days to schedule payment. 15 days ahead of limit.
    """
    quantity = int(quantity)
    if 1 <= quantity <= 15:
        payment_date = (datetime.today() + timedelta(days=quantity)).strftime('%Y-%m-%d')
        return get_translation("payment_scheduled", name=name, payment_date=payment_date)
    else:
        return get_translation("error_quantity")