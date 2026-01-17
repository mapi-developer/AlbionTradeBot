import flet as ft
import webbrowser
import threading
import http.server
import socketserver
from urllib.parse import urlparse, parse_qs
import urllib.parse
from typing import Optional
import sys, os
import base64

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gui.components.style import GuiStyle
from bot import SettingsHandler


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

        if "access_token" in params and "user_id" in params:
            self.server.token = params.get("access_token")[0]
            self.server.user_id = params.get("user_id")[0]

            # Send a nice HTML response to the browser
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(
                b"""
                <html>
                <body style='background-color:#131415; color:white; font-family:sans-serif; text-align:center; padding-top:50px;'>
                    <h1>Login Successful!</h1>
                    <p>You can close this window and return to the bot.</p>
                    <script>window.close();</script>
                </body>
                </html>
            """
            )

            # Stop the server in a separate thread to avoid deadlock
            threading.Thread(target=self.server.shutdown, daemon=True).start()
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Login failed: Missing token.")

    def log_message(self, format, *args):
        # Override to prevent printing to stdout/console
        return


class Login(ft.Container):
    def __init__(
        self, page: ft.Page, on_login_success, settings: SettingsHandler
    ):
        super().__init__()
        self.settings = settings
        self.page = page
        self.expand = True
        self.bgcolor = GuiStyle.Colors.DARK_BLUE
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
            redirect_uri = f"{self.settings.API_URL}/login/{provider}"
            state_param = urllib.parse.quote(self.settings.LOCAL_REDIRECT_URI)

            if provider == "google":
                params = {
                    "client_id": self.settings.GOOGLE_CLIENT_ID,
                    "redirect_uri": redirect_uri,
                    "response_type": "code",
                    "scope": "openid email profile",
                    "access_type": "offline",
                    "state": state_param,
                }
                query_string = urllib.parse.urlencode(params)
                auth_url = (
                    f"https://accounts.google.com/o/oauth2/v2/auth?{query_string}"
                )

            elif provider == "discord":
                params = {
                    "client_id": self.settings.DISCORD_CLIENT_ID,
                    "redirect_uri": redirect_uri,
                    "response_type": "code",
                    "scope": "identify email",
                    "state": state_param,
                }
                query_string = urllib.parse.urlencode(params)
                auth_url = f"https://discord.com/api/oauth2/authorize?{query_string}"

            print(f"Opening browser for {provider} login...")
            webbrowser.open(auth_url)

        google_svg = """
        <svg version="1.1" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" style="display: block;">
            <path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"></path>
            <path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"></path>
            <path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"></path>
            <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"></path>
            <path fill="none" d="M0 0h48v48H0z"></path>
        </svg>
        """

        discord_svg = """
        <svg width="800px" height="800px" viewBox="0 -28.5 256 256" version="1.1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" preserveAspectRatio="xMidYMid">
            <g>
                <path d="M216.856339,16.5966031 C200.285002,8.84328665 182.566144,3.2084988 164.041564,0 C161.766523,4.11318106 159.108624,9.64549908 157.276099,14.0464379 C137.583995,11.0849896 118.072967,11.0849896 98.7430163,14.0464379 C96.9108417,9.64549908 94.1925838,4.11318106 91.8971895,0 C73.3526068,3.2084988 55.6133949,8.86399117 39.0420583,16.6376612 C5.61752293,67.146514 -3.4433191,116.400813 1.08711069,164.955721 C23.2560196,181.510915 44.7403634,191.567697 65.8621325,198.148576 C71.0772151,190.971126 75.7283628,183.341335 79.7352139,175.300261 C72.104019,172.400575 64.7949724,168.822202 57.8887866,164.667963 C59.7209612,163.310589 61.5131304,161.891452 63.2445898,160.431257 C105.36741,180.133187 151.134928,180.133187 192.754523,160.431257 C194.506336,161.891452 196.298154,163.310589 198.110326,164.667963 C191.183787,168.842556 183.854737,172.420929 176.223542,175.320965 C180.230393,183.341335 184.861538,190.991831 190.096624,198.16893 C211.238746,191.588051 232.743023,181.531619 254.911949,164.955721 C260.227747,108.668201 245.831087,59.8662432 216.856339,16.5966031 Z M85.4738752,135.09489 C72.8290281,135.09489 62.4592217,123.290155 62.4592217,108.914901 C62.4592217,94.5396472 72.607595,82.7145587 85.4738752,82.7145587 C98.3405064,82.7145587 108.709962,94.5189427 108.488529,108.914901 C108.508531,123.290155 98.3405064,135.09489 85.4738752,135.09489 Z M170.525237,135.09489 C157.88039,135.09489 147.510584,123.290155 147.510584,108.914901 C147.510584,94.5396472 157.658606,82.7145587 170.525237,82.7145587 C183.391518,82.7145587 193.761324,94.5189427 193.539891,108.914901 C193.539891,123.290155 183.391518,135.09489 170.525237,135.09489 Z" fill="#5865F2" fill-rule="nonzero">

        </path>
            </g>
        </svg>
        """

        svg_base64_google = base64.b64encode(google_svg.encode('utf-8')).decode('utf-8')
        svg_base64_discord = base64.b64encode(discord_svg.encode('utf-8')).decode('utf-8')

        self.login_card = ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        value="Welcome to",
                        size=20,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER,
                        color=ft.Colors.WHITE,
                    ),
                    ft.Text(
                        value="Market Trader",
                        size=30,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER,
                        color=ft.Colors.WHITE,
                    ),
                    ft.Text("Log in to continue", size=12, color=ft.Colors.WHITE70),
                    self.error_text,  # Error message area
                    ft.ElevatedButton(
                        width=280,
                        bgcolor=ft.Colors.WHITE,
                        color=ft.Colors.BLACK,
                        style=ft.ButtonStyle(
                            padding=20,
                            side=ft.BorderSide(
                                0.8, "#b1afaf", ft.BorderSideStrokeAlign.OUTSIDE
                            ),
                            shape=ft.RoundedRectangleBorder(radius=15),
                        ),
                        content=ft.Row(
                            [
                                ft.Image(src_base64=svg_base64_google, width=24, height=24),
                                ft.Text("LogIn with Google", size=16, weight=ft.FontWeight.W_500),
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=10
                        ),
                        expand=True,
                        data="google",
                        on_click=on_login_click,
                    ),
                    ft.ElevatedButton(
                        width=280,
                        bgcolor=ft.Colors.WHITE,
                        color=ft.Colors.BLACK,
                        style=ft.ButtonStyle(
                            padding=20,
                            side=ft.BorderSide(
                                0.8, "#b1afaf", ft.BorderSideStrokeAlign.OUTSIDE
                            ),
                            shape=ft.RoundedRectangleBorder(radius=15),
                        ),
                        content=ft.Row(
                            [
                                ft.Image(src_base64=svg_base64_discord, width=24, height=24),
                                ft.Text("LogIn with Discord", size=16, weight=ft.FontWeight.W_500),
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=10
                        ),
                        expand=True,
                        data="discord",
                        on_click=on_login_click,
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
            ),
            width=350,
            padding=40,
            bgcolor=GuiStyle.Colors.LIGHT_BLUE,
            border_radius=ft.border_radius.all(20),
            border=ft.border.all(width=1, color=ft.Colors.WHITE70),
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=10,
                color=ft.Colors.WHITE70,
                offset=ft.Offset(0, 0),
                blur_style=ft.ShadowBlurStyle.OUTER,
            ),
            alignment=ft.alignment.center,
        )

        self.content = ft.Container(
            content=ft.Column(
                controls=[self.login_card], alignment=ft.alignment.center
            ),
            alignment=ft.alignment.center,
            bgcolor=ft.Colors.TRANSPARENT,
            padding=50,
            margin=50,
            expand=True,
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
            with socketserver.TCPServer(
                ("127.0.0.1", self.settings.LOCAL_AUTH_PORT), OAuthHandler
            ) as httpd:
                print(
                    f"Local auth server listening on port {self.settings.LOCAL_AUTH_PORT}..."
                )
                httpd.token = None
                httpd.user_id = None

                # Block here until shutdown() is called in do_GET
                httpd.serve_forever()

                # Logic after server stops
                if httpd.token and httpd.user_id:
                    print("Token received!")
                    self.state.token = httpd.token
                    self.state.user_id = httpd.user_id

                    # Save credentials to settings.json so they persist after restart
                    self.settings.set("auth_token", httpd.token)
                    self.settings.set("user_id", httpd.user_id)

                    # Call the success callback
                    if self.on_login_success:
                        self.on_login_success()
        except OSError as e:
            print(f"Failed to start auth server: {e}")
            self.error_text.value = f"Error: Port {self.settings.LOCAL_AUTH_PORT} is busy. Close other bot instances."
            self.error_text.visible = True
            self.page.update()
        except Exception as e:
            print(f"Unexpected server error: {e}")
        finally:
            self.server_running = False
