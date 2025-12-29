import requests
import time
import random

# CONFIGURATION
# ------------------------------------------------------
# Replace this with your actual Cloud Run URL
API_URL = "https://trade-backend-service-1054089939982.europe-west4.run.app" 
# API_URL = "http://localhost:8080" # Use this if testing locally

def test_price_update_flow():
    print(f"--- 1. Testing Connection to {API_URL} ---")
    try:
        r = requests.get(f"{API_URL}/")
        if r.status_code == 200:
            print("✅ API is online.")
        else:
            print(f"❌ API returned status {r.status_code}")
            return
    except Exception as e:
        print(f"❌ Could not connect: {e}")
        return

    # ------------------------------------------------------
    print("\n--- 2. Sending Price Updates (Bot Simulation) ---")
    
    # Create random prices to verify we are really updating values
    price_caerleon = random.randint(1000, 5000)
    price_martlock = random.randint(1000, 5000)
    
    payload = [
        {
            "unique_name": "TEST_SWORD_T4",
            "price_caerleon": price_caerleon
        },
        {
            "unique_name": "TEST_SHIELD_T4",
            "price_martlock": price_martlock
        }
    ]
    
    print(f"Sending: TEST_SWORD_T4 -> Caerleon: {price_caerleon}")
    print(f"Sending: TEST_SHIELD_T4 -> Martlock: {price_martlock}")

    try:
        # Hitting the endpoint defined in main.py: PUT /items/prices
        response = requests.put(f"{API_URL}/items/prices", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Update Queued! Server response: {data}")
        else:
            print(f"❌ Update Failed: {response.text}")
            return
    except Exception as e:
        print(f"❌ Request Error: {e}")
        return

    # ------------------------------------------------------
    print("\n--- 3. Triggering Buffer Flush (System Simulation) ---")
    # In production, Cloud Scheduler does this every minute.
    # We force it here to see results immediately.
    
    try:
        flush_res = requests.post(f"{API_URL}/system/flush-buffer")
        print(f"Flush Response: {flush_res.json()}")
    except Exception as e:
        print(f"⚠️  Flush trigger failed (might need to wait for auto-scheduler): {e}")

    # ------------------------------------------------------
    print("\n--- 4. Verifying Data (Read Check) ---")
    # Waiting a brief moment for DB commit
    time.sleep(1)
    
    try:
        # Fetching the items back to see if prices match
        # Hitting the endpoint defined in main.py: GET /items/
        params = {"item_names": ["TEST_SWORD_T4", "TEST_SHIELD_T4"]}
        read_res = requests.get(f"{API_URL}/items/", params=params)
        
        items = read_res.json()
        
        # Verify SWORD
        sword = next((i for i in items if i['unique_name'] == "TEST_SWORD_T4"), None)
        if sword and sword['price_caerleon'] == price_caerleon:
            print(f"✅ SUCCESS: TEST_SWORD_T4 Caerleon price is {sword['price_caerleon']}")
        else:
            print(f"❌ FAIL: Expected {price_caerleon}, got {sword.get('price_caerleon') if sword else 'None'}")

        # Verify SHIELD
        shield = next((i for i in items if i['unique_name'] == "TEST_SHIELD_T4"), None)
        if shield and shield['price_martlock'] == price_martlock:
            print(f"✅ SUCCESS: TEST_SHIELD_T4 Martlock price is {shield['price_martlock']}")
        else:
            print(f"❌ FAIL: Expected {price_martlock}, got {shield.get('price_martlock') if shield else 'None'}")

    except Exception as e:
        print(f"❌ Read Error: {e}")

if __name__ == "__main__":
    test_price_update_flow()