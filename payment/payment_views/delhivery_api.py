import requests
import json
from django.conf import settings


# ==============================================
# create Order
# ==============================================

def create_delhivery_order(order_data):
    """Create an order in Delhivery using the provided order data."""
    url = "https://track.delhivery.com/api/cmu/create.json"
    headers = {
        "Authorization": f"Token {settings.DELHIVERY_API_KEY}",
        "Content-Type": "application/x-www-form-urlencoded"  # Changed to x-www-form-urlencoded
    }
    
    print(order_data,"************************")
    # Prepare the payload
    # payload = {
    #     "shipments": [
    #         {
    #             "name": order_data['name'],
    #             "add": order_data['address'],
    #             "pin": order_data['pincode'],
    #             "city": order_data['city'],
    #             "state": order_data['state'],
    #             "country": "India",
    #             "phone": order_data['phone'],
    #             "order": order_data['order_id'],
    #             "payment_mode": "COD" ,
    #             "products_desc": order_data['product_description'],
    #             "cod_amount": order_data['cod_amount'] ,
    #             "shipping_mode": "Surface",
    #             "address_type": "home"
    #         }
    #     ],
    #     "pickup_location": {
    #         "name": "TREERANGA",  
    #         "add": "badambadi",
    #         "city": "jajpur",
    #         "pin_code": "755043",
    #         "country": "India",
    #         "phone": "8310418179"
    #     }
    # }
    # print(payload,"order_data==================")
    # Format the payload as a string
    formatted_payload = f'format=json&data={json.dumps(order_data, default=str)}'

    # Log the payload being sent
    print("Sending payload to Delhivery:", formatted_payload)

    try:
        # Send request to Delhivery API
        response = requests.post(url, data=formatted_payload, headers=headers)
        response.raise_for_status()  # Raise exception for bad responses

        response_data = response.json()

        # Debugging information
        print(f"Response Status Code: {response.status_code}")
        print(f"Response Content: {json.dumps(response_data, indent=2)}")

        # Check for the waybill number
        # if 'packages' in response_data and response_data['packages']:
        #     waybill_number = response_data['packages'][0].get('waybill')
        #     return {"success": True, "waybill": waybill_number}
        # else:
        #     return {"success": False, "message": "Failed to create order in Delhivery: 'packages' key missing or empty."}
    
    except requests.RequestException as e:
        return {"success": False, "message": f"Error during order creation in Delhivery: {str(e)}"}
    
    
    
# ==============================================
# track order Order
# ==============================================


def track_delhivery_order(waybill=None, ref_id=None):
    """Track an order using Delhivery API."""
    url = "https://track.delhivery.com/api/v1/packages/json/"
    params = {}
    
    # Track either by waybill or reference number (ref_id)
    if waybill:
        params["waybill"] = waybill
    if ref_id:
        params["ref_ids"] = ref_id

    headers = {
        "Authorization": f"Token {settings.DELHIVERY_API_KEY}"
    }

    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        response_data = response.json()

        # Check if the response contains the tracking data
        if "ShipmentData" in response_data and len(response_data["ShipmentData"]) > 0:
            return {"success": True, "data": response_data["ShipmentData"]}
        else:
            return {"success": False, "message": "No tracking data found"}
    
    except requests.RequestException as e:
        return {"success": False, "message": f"Error during tracking: {str(e)}"}

# ==============================================
# Cancel Order
# ==============================================

def cancel_delhivery_order(waybill):
    """Cancel an order using the Delhivery API."""
    url = "https://staging-express.delhivery.com/api/p/edit"  # Use the correct cancellation URL
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Token {settings.DELHIVERY_API_KEY}"  # Use your API token here
    }

    payload = {
        "waybill": waybill,
        "cancellation": True
    }

    print("Sending cancellation request to Delhivery:", json.dumps(payload, indent=2))

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        response_data = response.json()

        print(f"Cancellation Response Status Code: {response.status_code}")
        print(f"Cancellation Response Content: {json.dumps(response_data, indent=2)}")

        if response_data.get('success', False):
            return {"success": True, "message": "Order cancelled successfully."}
        else:
            return {"success": False, "message": response_data.get('message', 'Failed to cancel order.')}
    
    except requests.RequestException as e:
        return {"success": False, "message": f"Error during order cancellation: {str(e)}"}
    


# ==============================================
# Check pin service
# ==============================================
    
def check_pincode_serviceability(pincode):
    """Check if the given pincode is serviceable by Delhivery."""
    # Use the production environment URL
    url = f"https://track.delhivery.com/c/api/pin-codes/json/?filter_codes={pincode}"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Token {settings.DELHIVERY_API_KEY}"  # Use your API token here
    }

    try:
        response = requests.get(url, headers=headers)  # Use GET method for fetching serviceability
        response.raise_for_status()
        response_data = response.json()

        # Assuming the API response contains serviceability details
        # Check if the response contains 'serviceable' or equivalent keys
        if 'serviceability' in response_data and isinstance(response_data['serviceability'], dict):
            # Depending on the response structure, modify the following line
            return response_data['serviceability'].get('serviceable', False)
        else:
            return False  # If the API indicates failure, treat as non-serviceable

    except requests.RequestException as e:
        return {"success": False, "message": f"Error checking pincode serviceability: {str(e)}"}