import requests
import hmac
import hashlib
import json
import random

# --- CONFIGURATION ---
# 1. Your Backend URL
WEBHOOK_URL = "https://trade-backend-service-1054089939982.europe-west4.run.app/payments/webhook"

# 2. Your REAL Secret (Must match what is in Cloud Run secrets)
IPN_SECRET = "njOn360PKnEiScgzGTgA2cHbR9vsSsCE" 

# 3. The User ID you want to upgrade
USER_ID = 3
DAYS_TO_ADD = 30 # Simulate a 1-month plan

def force_payment_success():
    print(f"🚀 Simulating payment for User {USER_ID}...")

    # Generate a random Invoice ID (or use a real one from your DB to test status update)
    fake_invoice_id = random.getrandbits(32)

    # UPDATED PAYLOAD: 
    # 1. Added 'id' (Integer) -> Required by your backend `int(data.get('id'))`
    # 2. 'order_id' -> Used to identify the User and Duration
    payload = {
        "id": fake_invoice_id,           # <--- CRITICAL CHANGE: Must be an Integer
        "payment_status": "finished",
        "pay_address": "TQn9...",
        "price_amount": 50,
        "price_currency": "usd",
        "pay_amount": 50,
        "pay_currency": "usdttrc20",
        "order_id": f"{USER_ID}::{DAYS_TO_ADD}", 
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
            print(f"User {USER_ID} should now be Premium (added {DAYS_TO_ADD} days).")
            print(f"Simulated Invoice ID used: {fake_invoice_id}")
        else:
            print(f"❌ FAILED. Status: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    force_payment_success()