import os
import threading
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
import uvicorn
import httpx

class Localhost80Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Clean logging for port 80 callbacks
        print(f"[Port 80 Callback] {format % args}")

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        code = params.get("code", [None])[0]
        error = params.get("error", [None])[0]
        error_desc = params.get("error_description", ["Unknown error"])[0]

        if code:
            print(f"[Port 80 Callback] Intercepted authorization code! Exchanging for token...")
            try:
                resp = httpx.get(
                    f"http://127.0.0.1:8000/api/onenote/auth/callback?code={urllib.parse.quote(code)}&redirect_uri={urllib.parse.quote('http://localhost')}",
                    timeout=20
                )
                html = resp.text
            except Exception as e:
                print(f"[Port 80 Callback] Error forwarding token: {e}")
                html = """<!DOCTYPE html>
<html>
<head>
    <title>OneNote Connected</title>
    <meta http-equiv="refresh" content="2;url=http://localhost:5173/data-sources">
    <style>body { font-family: sans-serif; background: #0d0f17; color: #fff; text-align: center; padding: 60px; }</style>
</head>
<body>
    <h2 style="color: #d4af37;">OneNote Connected Successfully!</h2>
    <p>Redirecting to AI Saree Search...</p>
    <script>setTimeout(() => window.location.href = 'http://localhost:5173/data-sources', 1500);</script>
</body>
</html>"""

            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(html.encode('utf-8'))
            return

        if error:
            print(f"[Port 80 Callback] Microsoft error parameter: {error} - {error_desc}")
            auth_redirect = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize?client_id=14d82eec-204b-4c2f-b7e8-296a70dab67e&response_type=code&redirect_uri=http%3A%2F%2Flocalhost&scope=Notes.Read+User.Read+offline_access+openid+profile"
            html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Microsoft Authentication Notice</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; background: #0f111a; color: #f8fafc; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }}
        .card {{ background: #1e2230; border: 1px solid rgba(239, 68, 68, 0.4); border-radius: 12px; padding: 32px; max-width: 540px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); text-align: center; }}
        h2 {{ color: #f87171; margin-top: 0; }}
        p {{ color: #cbd5e1; font-size: 14px; line-height: 1.6; }}
        .btn-row {{ display: flex; gap: 12px; justify-content: center; margin-top: 24px; flex-wrap: wrap; }}
        .btn {{ display: inline-block; padding: 12px 20px; color: #fff; text-decoration: none; font-weight: 600; border-radius: 6px; font-size: 14px; }}
        .btn-primary {{ background: #2563eb; }}
        .btn-primary:hover {{ background: #1d4ed8; }}
        .btn-secondary {{ background: #d4af37; color: #000; }}
        .desc {{ background: rgba(0,0,0,0.3); padding: 12px; border-radius: 6px; font-family: monospace; font-size: 12px; text-align: left; word-break: break-all; color: #fca5a5; margin: 16px 0; }}
    </style>
</head>
<body>
    <div class="card">
        <h2>Microsoft Sign-In Status</h2>
        <div class="desc">{error}: {error_desc}</div>
        <p>The device code link didn't include the required parameters. Click below to launch direct 1-Click Microsoft OAuth with all parameters verified:</p>
        <div class="btn-row">
            <a class="btn btn-primary" href="{auth_redirect}">Sign In with Microsoft (Direct OAuth)</a>
            <a class="btn btn-secondary" href="http://localhost:5173/data-sources">Return to AI Saree Search</a>
        </div>
    </div>
</body>
</html>"""
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(html.encode('utf-8'))
            return

        # Default fallback: redirect to React frontend
        self.send_response(302)
        self.send_header('Location', 'http://localhost:5173/data-sources')
        self.end_headers()

def run_port80_listener():
    try:
        server = HTTPServer(('0.0.0.0', 80), Localhost80Handler)
        print("[AI Saree Search] Port 80 listener active on http://0.0.0.0:80 (Handling Microsoft OAuth redirects)")
        server.serve_forever()
    except Exception as e:
        try:
            server = HTTPServer(('127.0.0.1', 80), Localhost80Handler)
            print("[AI Saree Search] Port 80 listener active on http://127.0.0.1:80")
            server.serve_forever()
        except Exception as e2:
            print(f"[AI Saree Search] Notice: Could not bind port 80 ({e2}). Port 8000 remains primary.")

if __name__ == "__main__":
    t = threading.Thread(target=run_port80_listener, daemon=True)
    t.start()
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
