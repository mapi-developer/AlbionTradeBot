import flet as ft
import webbrowser
import threading
import http.server
import socketserver
from urllib.parse import urlparse, parse_qs
import urllib.parse
from typing import Optional

API_URL = "https://crypto-backend-736893217724.europe-west3.run.app"
GOOGLE_CLIENT_ID = "736893217724-2q2tqloh51meq7c6oklt7apk9jqfm5vt.apps.googleusercontent.com"
DISCORD_CLIENT_ID = "1447721013260456058"
LOCAL_AUTH_PORT = 5000 
LOCAL_REDIRECT_URI = f"http://127.0.0.1:{LOCAL_AUTH_PORT}/oauth/callback" 

class State:
    token: Optional[str] = None
    user_id: Optional[str] = None

class OAuthHandler(http.server.SimpleHTTPRequestHandler):
    """Handles the final callback from the Cloud Backend."""
    
    def do_GET(self):
        # Silence the console logs for requests
        pass

        query = urlparse(self.path).query
        params = parse_qs(query)
        
        if 'access_token' in params and 'user_id' in params:
            self.server.token = params.get('access_token')[0]
            self.server.user_id = params.get('user_id')[0]
            
            # Send a nice HTML response to the browser
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"""
                <html>
                <body style='background-color:#131415; color:white; font-family:sans-serif; text-align:center; padding-top:50px;'>
                    <h1>Login Successful!</h1>
                    <p>You can close this window and return to the bot.</p>
                    <script>window.close();</script>
                </body>
                </html>
            """)
            
            # Stop the server in a separate thread to avoid deadlock
            threading.Thread(target=self.server.shutdown, daemon=True).start()
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'Login failed: Missing token.')

    def log_message(self, format, *args):
        # Override to prevent printing to stdout/console
        return

class Login(ft.Container):
    def __init__(self, page: ft.Page, on_login_success):
        super().__init__()
        self.page = page
        self.expand = True
        self.bgcolor = "#174e7e"
        self.state = State()
        self.on_login_success = on_login_success
        self.server_running = False

        self.error_text = ft.Text("", color=ft.Colors.RED, size=12, visible=False)

        def on_login_click(event):
            # Reset error text
            self.error_text.visible = False
            self.error_text.value = ""
            self.page.update()

            provider = event.control.data
            
            # Start the local server in a background thread
            threading.Thread(target=self.start_local_server, daemon=True).start()

            # Construct Auth URL
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

            print(f"Opening browser for {provider} login...")
            webbrowser.open(auth_url)

        self.login_card = ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        value="Welcome to Albion Trade Bot",
                        size=30,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER,
                        color=ft.Colors.BLACK,
                    ),
                    ft.Text("Log in to continue", size=12, color=ft.Colors.GREY),
                    self.error_text, # Error message area
                    ft.ElevatedButton(
                        text="LogIn with Google",
                        width=280,
                        bgcolor=ft.Colors.BLUE,
                        color=ft.Colors.WHITE,
                        style=ft.ButtonStyle(padding=20),
                        expand=True,
                        data="google",
                        on_click=on_login_click
                    ),
                    ft.ElevatedButton(
                        text="LogIn with Discord",
                        width=280,
                        bgcolor="#4334ca",
                        color=ft.Colors.WHITE,
                        style=ft.ButtonStyle(padding=20),
                        expand=True,
                        data="discord",
                        on_click=on_login_click
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
            ),
            width=350,
            padding=40,
            bgcolor=ft.Colors.WHITE,
            border_radius=ft.border_radius.all(20),
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=10,
                color=ft.Colors.BLUE_GREY_300,
                offset=ft.Offset(0, 0),
                blur_style=ft.ShadowBlurStyle.OUTER,
            ),
            alignment=ft.alignment.center
        )

        self.content = ft.Container(
            content=ft.Column(controls=[self.login_card], alignment=ft.alignment.center),
            alignment=ft.alignment.center,
            bgcolor=ft.Colors.TRANSPARENT,
            padding=50,
            margin=50,
            expand=True
        )

    def start_local_server(self):
        """Starts a temporary HTTP server to listen for the OAuth callback."""
        if self.server_running:
            print("Server already running.")
            return

        self.server_running = True
        try:
            socketserver.TCPServer.allow_reuse_address = True
            # Attempt to bind to port 5000
            with socketserver.TCPServer(("127.0.0.1", LOCAL_AUTH_PORT), OAuthHandler) as httpd:
                print(f"Local auth server listening on port {LOCAL_AUTH_PORT}...")
                httpd.token = None
                httpd.user_id = None
                
                # Block here until shutdown() is called in do_GET
                httpd.serve_forever()
                
                # Logic after server stops
                if httpd.token and httpd.user_id:
                    print("Token received!")
                    self.state.token = httpd.token
                    self.state.user_id = httpd.user_id
                    
                    # Call the success callback
                    if self.on_login_success:
                        self.on_login_success()
        except OSError as e:
            print(f"Failed to start auth server: {e}")
            self.error_text.value = f"Error: Port {LOCAL_AUTH_PORT} is busy. Close other bot instances."
            self.error_text.visible = True
            self.page.update()
        except Exception as e:
            print(f"Unexpected server error: {e}")
        finally:
            self.server_running = False