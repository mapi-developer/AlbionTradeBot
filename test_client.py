import flet as ft
import requests
import webbrowser
import threading
import time
import http.server
import socketserver
from urllib.parse import urlparse, parse_qs
import urllib.parse
from typing import Optional

# --- CONFIGURATION (FILL THESE IN) ---
# 1. Your Cloud Run URL (No trailing slash)
API_URL = "https://crypto-backend-736893217724.europe-west3.run.app" 

# 2. Your OAuth Client IDs 
GOOGLE_CLIENT_ID = "736893217724-2q2tqloh51meq7c6oklt7apk9jqfm5vt.apps.googleusercontent.com"
DISCORD_CLIENT_ID = "1447721013260456058"

# LOCAL SERVER SETUP
LOCAL_AUTH_PORT = 5000 
LOCAL_REDIRECT_URI = f"http://127.0.0.1:{LOCAL_AUTH_PORT}/oauth/callback" 


class State:
    token: Optional[str] = None
    user_id: Optional[str] = None

state = State()

# --- LOCAL SERVER HANDLER ---

class OAuthHandler(http.server.SimpleHTTPRequestHandler):    
    def do_GET(self):
        query = urlparse(self.path).query
        params = parse_qs(query)
        
        if 'access_token' in params and 'user_id' in params:
            self.server.token = params.get('access_token')[0]
            self.server.user_id = params.get('user_id')[0]
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'<p>Login successful! You can close this window now.</p><script>window.close();</script>')
            
            threading.Thread(target=self.server.shutdown).start()
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'Login failed or token not found.')


def start_local_server(page, check_subscription_func):
    try:
        socketserver.TCPServer.allow_reuse_address = True
        
        with socketserver.TCPServer(("127.0.0.1", LOCAL_AUTH_PORT), OAuthHandler) as httpd:
            httpd.token = None
            httpd.user_id = None
            
            httpd.serve_forever()
            
            if httpd.token and httpd.user_id:
                state.token = httpd.token
                state.user_id = httpd.user_id
                
                page.snack_bar = ft.SnackBar(content=ft.Text("✅ Login successful! Checking subscription..."))
                page.snack_bar.open = True
                page.update()
                
                check_subscription_func()
            else:
                page.snack_bar = ft.SnackBar(content=ft.Text("❌ Login failed or timed out."))
                page.snack_bar.open = True
                page.update()
            
    except OSError as e:
        page.snack_bar = ft.SnackBar(content=ft.Text(f"Server error: {e}. Port {LOCAL_AUTH_PORT} in use."))
        page.snack_bar.open = True
        page.update()


# --- FLET APPLICATION ---

def main(page: ft.Page):
    page.title = "Crypto Subscription App"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 450
    page.window_height = 800
    page.padding = 20

    # --- UI ELEMENTS ---
    txt_status = ft.Text("Not Logged In", color=ft.Colors.RED, weight=ft.FontWeight.BOLD)
    txt_sub_status = ft.Text("Subscription: Unknown")
    
    def check_subscription():
        """Calls the backend to see if user is premium."""
        if not state.user_id or not state.token: 
            txt_status.value = "Not Logged In"
            txt_status.color = ft.Colors.RED
            page.update()
            return
        
        headers = {"Authorization": f"Bearer {state.token}"}
        try:
            res = requests.get(f"{API_URL}/users/{state.user_id}", headers=headers)
            
            if res.status_code == 200:
                data = res.json()
                sub_date = data.get("subscribed_until")
                
                if sub_date:
                    clean_date = sub_date.split("T")[0]
                    txt_sub_status.value = f"✅ PREMIUM until: {clean_date}"
                    txt_sub_status.color = ft.Colors.GREEN
                    btn_pay.visible = False
                    container_premium.visible = True
                else:
                    txt_sub_status.value = "⚠️ Free Plan (Expired)"
                    txt_sub_status.color = ft.Colors.YELLOW
                    btn_pay.visible = True
                    container_premium.visible = False
                
                txt_status.value = f"Logged in as User {state.user_id}"
                page.update()
            
            elif res.status_code == 404:
                 txt_status.value = f"Token invalid or User not found."
            
            page.update()
            
        except Exception as e:
            txt_status.value = "Connection Error"
            print(f"Connection error during status check: {e}")
            page.update()


    def login_click(e, provider):
        """Starts local server and opens browser."""
        # Start the local server listener in a background thread
        threading.Thread(target=start_local_server, args=(page, check_subscription), daemon=True).start()

        redirect_uri = f"{API_URL}/auth/login/{provider}"
        state_param = urllib.parse.quote(LOCAL_REDIRECT_URI)

        if provider == "google":
            params = {
                "client_id": GOOGLE_CLIENT_ID,
                "redirect_uri": redirect_uri,
                "response_type": "code",
                "scope": "openid email profile",
                "access_type": "offline",
                "state": state_param 
            }
            query_string = urllib.parse.urlencode(params)
            auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{query_string}"
            
        elif provider == "discord":
            params = {
                "client_id": DISCORD_CLIENT_ID,
                "redirect_uri": redirect_uri,
                "response_type": "code",
                "scope": "identify email",
                "state": state_param
            }
            query_string = urllib.parse.urlencode(params)
            auth_url = f"https://discord.com/api/oauth2/authorize?{query_string}"

        webbrowser.open(auth_url)
        
        page.snack_bar = ft.SnackBar(content=ft.Text(f"Waiting for login via {provider.capitalize()}..."))
        page.snack_bar.open = True
        page.update()


    def pay_click(e):
        """Starts payment flow"""
        if not state.user_id or not state.token: 
            page.snack_bar = ft.SnackBar(content=ft.Text("Log in first to initiate payment!"))
            page.snack_bar.open = True
            page.update()
            return

        btn_pay.text = "Generating Link..."
        btn_pay.disabled = True
        page.update()

        try:
            res = requests.post(f"{API_URL}/payments/create", 
                                params={"user_id": state.user_id, "plan_id": "1_month"})
            
            if res.status_code == 200:
                data = res.json()
                webbrowser.open(data.get("invoice_url"))
                btn_pay.text = "Waiting for Payment..."
                threading.Thread(target=poll_payment_status, daemon=True).start()
            else:
                btn_pay.text = "Failed"
                print(res.text)

        except Exception as ex:
            btn_pay.text = "Error"
            print(ex)
        page.update()

    def poll_payment_status():
        """Checks subscription status every 5 seconds (runs in background thread)."""
        for _ in range(60): 
            time.sleep(5)
            # Safe to call because check_subscription calls page.update() which is thread-safe
            check_subscription() 
            if "PREMIUM" in txt_sub_status.value:
                break


    # --- LAYOUT COMPONENTS ---
    
    btn_google = ft.ElevatedButton(
        "Login with Google", 
        icon=ft.Icons.LOGIN, 
        on_click=lambda e: login_click(e, "google"),
        width=200
    )
    
    btn_discord = ft.ElevatedButton(
        "Login with Discord", 
        icon=ft.Icons.DISCORD, 
        on_click=lambda e: login_click(e, "discord"),
        width=200,
        style=ft.ButtonStyle(bgcolor=ft.Colors.INDIGO)
    )

    btn_pay = ft.ElevatedButton(
        "Subscribe ($10/mo)", 
        on_click=pay_click, 
        icon=ft.Icons.CURRENCY_BITCOIN,
        style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE),
        height=50
    )

    container_premium = ft.Container(
        content=ft.Column([
            ft.Icon(ft.Icons.LOCK_OPEN, size=40, color=ft.Colors.GREEN),
            ft.Text("Premium Features Unlocked!", size=20, weight=ft.FontWeight.BOLD),
            ft.Text("You can now use the trade bot functions."),
            ft.ElevatedButton("Start Bot", icon=ft.Icons.PLAY_ARROW)
        ]),
        visible=False,
        bgcolor=ft.Colors.BLUE_GREY_900,
        padding=20,
        border_radius=10
    )

    page.add(
        ft.Column([
            ft.Text("Step 1: Automatic Authentication", size=16, weight=ft.FontWeight.BOLD),
            ft.Row([btn_google, btn_discord], alignment=ft.MainAxisAlignment.CENTER),
            
            ft.Divider(),
            
            ft.Text("Status", size=16, weight=ft.FontWeight.BOLD),
            txt_status,
            txt_sub_status,
            ft.Container(height=10),
            
            btn_pay,
            ft.Container(height=20),
            container_premium
        ], alignment=ft.MainAxisAlignment.START)
    )

ft.app(target=main)