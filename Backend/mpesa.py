import requests
import base64
import datetime
from decouple import config
from requests.auth import HTTPBasicAuth

# --- Load credentials from .env ---
CONSUMER_KEY = config("MPESA_CONSUMER_KEY")
CONSUMER_SECRET = config("MPESA_CONSUMER_SECRET")
BUSINESS_SHORT_CODE = config("MPESA_SHORTCODE")  # e.g., "174379"
PASSKEY = config("MPESA_PASSKEY")
CALLBACK_URL = config("MPESA_CALLBACK_URL")  # e.g., ngrok URL

# --- Sandbox URLs ---
BASE_URL = "https://sandbox.safaricom.co.ke"
OAUTH_URL = f"{BASE_URL}/oauth/v1/generate?grant_type=client_credentials"
STK_PUSH_URL = f"{BASE_URL}/mpesa/stkpush/v1/processrequest"

# --- Generate access token ---
def generate_access_token():
    """Get OAuth access token from M-Pesa API."""
    response = requests.get(OAUTH_URL, auth=HTTPBasicAuth(CONSUMER_KEY, CONSUMER_SECRET), timeout=10)
    response.raise_for_status()  # Raises exception if request failed
    return response.json().get("access_token")


# --- Lipa na M-Pesa STK Push ---
def lipa_na_mpesa(phone_number, amount, account_reference="FitFlow Subscription", description="Subscription Payment"):
    """
    Initiates an STK Push to the specified phone number.
    """
    # Normalize phone number to 254 format
    phone_number = str(phone_number).replace(" ", "")
    if phone_number.startswith("0"):
        phone_number = "254" + phone_number[1:]
    elif phone_number.startswith("+"):
        phone_number = phone_number[1:]

    token = generate_access_token()
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    raw_password = BUSINESS_SHORT_CODE + PASSKEY + timestamp
    password = base64.b64encode(raw_password.encode()).decode()

    payload = {
        "BusinessShortCode": BUSINESS_SHORT_CODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": int(amount),
        "PartyA": phone_number,
        "PartyB": BUSINESS_SHORT_CODE,
        "PhoneNumber": phone_number,
        "CallBackURL": CALLBACK_URL,
        "AccountReference": account_reference,
        "TransactionDesc": description
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    response = requests.post(STK_PUSH_URL, json=payload, headers=headers, timeout=30)

    try:
        resp_json = response.json()
    except ValueError:
        resp_json = {"error": "Invalid response from M-Pesa", "text": response.text}

    print("STK Response:", resp_json)  # Debug output
    return resp_json
