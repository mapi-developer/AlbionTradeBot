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
        query = urlparse(self.path).query
        params = parse_qs(query)
        
        # Check if we received the token and user ID
        if 'access_token' in params and 'user_id' in params:
            self.server.token = params.get('access_token')[0]
            self.server.user_id = params.get('user_id')[0]
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'<p>Login successful! You can close this window now.</p><script>window.close();</script>')
            
            # Stop the local server
            threading.Thread(target=self.server.shutdown).start()
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'Login failed or token not found.')

class Login(ft.Container):
    def __init__(self, page: ft.Page, on_login_success):
        super().__init__()
        self.page=page
        self.expand = True
        self.bgcolor = "#174e7e"
        self.state = State()
        self.on_login_success = on_login_success

        def on_login_click(event):
            provider = event.control.data
            threading.Thread(target=self.start_local_server, args=(), daemon=True).start()

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
            
            page.update()

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
                    ft.ElevatedButton(
                        text="LogIn with Google",
                        width=280,
                        bgcolor=ft.Colors.BLUE,
                        color=ft.Colors.WHITE,
                        style=ft.ButtonStyle(
                            padding=ft.padding.only(0, 20, 0, 20)
                        ),
                        expand=True,
                        data="google",
                        on_click=on_login_click
                    ),
                    ft.ElevatedButton(
                        text="LogIn with Discord",
                        width=280,
                        bgcolor="#4334ca",
                        color=ft.Colors.WHITE,
                        style=ft.ButtonStyle(
                            padding=ft.padding.only(0, 20, 0, 20)
                        ),
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
            content=ft.Column(
                controls=[self.login_card], alignment=ft.alignment.center
            ),
            alignment=ft.alignment.center,
            bgcolor=ft.Colors.TRANSPARENT,
            padding=ft.padding.only(50, 50, 50, 50),
            margin=ft.margin.only(50, 50, 50, 50),
            expand=True
        )

    def start_local_server(self):
        try:
            socketserver.TCPServer.allow_reuse_address = True
            
            with socketserver.TCPServer(("127.0.0.1", LOCAL_AUTH_PORT), OAuthHandler) as httpd:
                httpd.token = None
                httpd.user_id = None
                
                httpd.serve_forever()
                
                if httpd.token and httpd.user_id:
                    self.state.token = httpd.token
                    self.state.user_id = httpd.user_id
                    
                    if self.on_login_success:
                        self.on_login_success()

                else:
                    self.page.update()
                
        except OSError as e:
            self.page.update()
