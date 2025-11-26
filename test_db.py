import psycopg2

try:
    # We explicitly use 127.0.0.1 to target Docker on Windows
    conn = psycopg2.connect(
        dbname="albion_market",
        user="albion_user",
        password="albion_password",
        host="127.0.0.1",
        port="5438"
    )
    print("✅ SUCCESS! Connected to Database.")
    conn.close()
except Exception as e:
    print(f"❌ FAILED: {e}")