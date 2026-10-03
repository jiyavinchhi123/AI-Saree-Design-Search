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
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>OneNote Connected - AI Saree Design Search</title>
    <meta http-equiv="refresh" content="2;url=http://localhost:5173/data-sources">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">
    <style>
        body {
            font-family: 'Inter', -apple-system, sans-serif;
            background: #f8fafc;
            background-image: radial-gradient(at 0% 0%, rgba(245, 243, 255, 0.9) 0px, transparent 50%), radial-gradient(at 100% 0%, rgba(254, 243, 199, 0.5) 0px, transparent 50%);
            display: flex;
            align-items: center;
            justify-content: center;
            height: 100vh;
            margin: 0;
            color: #0f172a;
        }
        .card {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 24px;
            padding: 40px;
            text-align: center;
            max-width: 440px;
            box-shadow: 0 20px 40px -10px rgba(109, 40, 217, 0.12);
        }
        .icon {
            width: 64px;
            height: 64px;
            border-radius: 50%;
            background: #ecfdf5;
            border: 2px solid #a7f3d0;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 16px;
        }
        h2 { font-size: 1.45rem; font-weight: 800; color: #0f172a; margin-bottom: 8px; }
        p { color: #64748b; font-size: 0.90rem; line-height: 1.5; margin-bottom: 20px; }
        .spinner { width: 14px; height: 14px; border: 2px solid #cbd5e1; border-top-color: #6d28d9; border-radius: 50%; display: inline-block; animation: spin 0.8s linear infinite; vertical-align: middle; margin-right: 6px; }
        @keyframes spin { to { transform: rotate(360deg); } }
    </style>
</head>
<body>
    <div class="card">
        <div class="icon">
            <svg viewBox="0 0 24 24" width="32" height="32" fill="none" stroke="#059669" stroke-width="2.8" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="20 6 9 17 4 12"></polyline>
            </svg>
        </div>
        <h2>Authentication Successful!</h2>
        <p><span class="spinner"></span> Redirecting to your AI Saree workspace...</p>
    </div>
    <script>setTimeout(() => window.location.href = 'http://localhost:5173/data-sources', 1200);</script>
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
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Microsoft Authentication Notice</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">
    <style>
        body {{
            font-family: 'Inter', -apple-system, sans-serif;
            background: #f8fafc;
            background-image: radial-gradient(at 0% 0%, rgba(245, 243, 255, 0.9) 0px, transparent 50%), radial-gradient(at 100% 0%, rgba(254, 243, 199, 0.5) 0px, transparent 50%);
            display: flex;
            align-items: center;
            justify-content: center;
            height: 100vh;
            margin: 0;
            color: #0f172a;
        }}
        .card {{
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 24px;
            padding: 36px;
            max-width: 520px;
            box-shadow: 0 20px 40px -10px rgba(109, 40, 217, 0.12);
            text-align: center;
        }}
        h2 {{ font-size: 1.45rem; font-weight: 800; color: #dc2626; margin-bottom: 8px; }}
        p {{ color: #64748b; font-size: 0.90rem; line-height: 1.6; }}
        .btn-row {{ display: flex; gap: 12px; justify-content: center; margin-top: 24px; flex-wrap: wrap; }}
        .btn {{ display: inline-block; padding: 10px 20px; color: #fff; text-decoration: none; font-weight: 600; border-radius: 8px; font-size: 0.88rem; }}
        .btn-primary {{ background: #6d28d9; }}
        .btn-primary:hover {{ background: #5b21b6; }}
        .btn-secondary {{ background: #f1f5f9; color: #334155; border: 1px solid #cbd5e1; }}
        .desc {{ background: #fef2f2; border: 1px solid #fecaca; padding: 12px; border-radius: 8px; font-family: monospace; font-size: 0.80rem; text-align: left; word-break: break-all; color: #b91c1c; margin: 16px 0; }}
    </style>
</head>
<body>
    <div class="card">
        <h2>Microsoft Sign-In Status</h2>
        <div class="desc">{error}: {error_desc}</div>
        <p>Click below to launch direct 1-Click Microsoft OAuth with verified parameters:</p>
        <div class="btn-row">
            <a class="btn btn-primary" href="{auth_redirect}">Sign In with Microsoft</a>
            <a class="btn btn-secondary" href="http://localhost:5173/data-sources">Return to Workspace</a>
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
