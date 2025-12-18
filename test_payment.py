import requests
import hmac
import hashlib
import json

# --- CONFIGURATION ---
# 1. Your Backend URL
WEBHOOK_URL = "https://crypto-backend-736893217724.europe-west3.run.app/payments/webhook"

# 2. Your REAL Secret (Must match what is in Cloud Run)
IPN_SECRET = "njOn360PKnEiScgzGTgA2cHbR9vsSsCE" 

# 3. The User ID you want to upgrade
USER_ID = 3
DAYS_TO_ADD = 30 # Simulate a 1-month plan

def force_payment_success():
    print(f"🚀 Simulating payment for User {USER_ID}...")

    # This is exactly what NOWPayments sends to your server
    payload = {
        "payment_id": "fake_test_tx_999",
        "payment_status": "finished",
        "pay_address": "TQn9...",
        "price_amount": 10.0,
        "price_currency": "usd",
        "pay_amount": 10.0,
        "pay_currency": "usdttrc20",
        "order_id": f"{USER_ID}::{DAYS_TO_ADD}", # Crucial: Matches your backend logic
        "created_at": "2024-12-14T12:00:00.000Z"
    }

    # Generate the Security Signature (HMAC)
    # Your backend checks this to ensure the request is not from a hacker
    sorted_data = json.dumps(payload, separators=(',', ':'), sort_keys=True)
    signature = hmac.new(
        key=IPN_SECRET.encode(),
        msg=sorted_data.encode(),
        digestmod=hashlib.sha512
    ).hexdigest()

    headers = {
        "x-nowpayments-sig": signature,
        "Content-Type": "application/json"
    }

    # Send the fake notification
    try:
        response = requests.post(WEBHOOK_URL, json=payload, headers=headers)
        
        if response.status_code == 200:
            print("✅ SUCCESS! Backend accepted the fake payment.")
            print(f"User {USER_ID} should now be Premium.")
        else:
            print(f"❌ FAILED. Status: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    force_payment_success()