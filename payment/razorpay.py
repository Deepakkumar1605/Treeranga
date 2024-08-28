import razorpay
from django.conf import settings

def create_order_in_razPay(amount,receipt="order_rcptid_12"):
    try:
        client = razorpay.Client(auth=(settings.RAZORPAY_API_KEY, settings.RAZORPAY_API_SECRET))
        data = {
            "amount": amount,
            "currency": "INR",
            "receipt": receipt,
            "partial_payment":False,
        }
        print(client)
        order = client.order.create(data=data)
        print(order)
        print("Order created successfully:", order)
        return (True, order['id'])
 
    except Exception as e:
        print(e)
        return (False, str(e))
 
def verify_signature(data):
    """
    Verify the payment signature using the Razorpay client utility.
    """
    client = razorpay.Client(auth=(settings.RAZORPAY_API_KEY, settings.RAZORPAY_API_SECRET))
    try:
        response_data = {
            'razorpay_order_id': data['razorpay_order_id'],
            'razorpay_payment_id': data['razorpay_payment_id'],
            'razorpay_signature': data['razorpay_signature']
        }
        return client.utility.verify_payment_signature(response_data)
    except KeyError as e:
        print(f"Key error: {e}")
        return False