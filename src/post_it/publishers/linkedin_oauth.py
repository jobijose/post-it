"""LinkedIn OAuth helpers.

Resolving the member URN is the only piece the publisher needs at runtime; the
full authorization-code flow is run once via ``post-it auth linkedin`` (see
:func:`run_local_auth_flow`).
"""

from __future__ import annotations

import http.server
import secrets
import threading
import urllib.parse
import webbrowser

import httpx

from post_it.exceptions import AuthError

USERINFO_URL = "https://api.linkedin.com/v2/userinfo"
AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
SCOPES = "openid profile w_member_social"
REDIRECT_URI = "http://localhost:8000/callback"


def fetch_author_urn(access_token: str) -> str:
    """Return the member URN (``urn:li:person:{sub}``) for ``access_token``."""
    try:
        resp = httpx.get(
            USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=15.0,
        )
        resp.raise_for_status()
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 401:
            raise AuthError("LinkedIn token is invalid or expired.") from exc
        raise AuthError(f"Failed to fetch LinkedIn userinfo: {exc}") from exc
    except httpx.HTTPError as exc:
        raise AuthError(f"Failed to reach LinkedIn userinfo: {exc}") from exc

    sub = resp.json().get("sub")
    if not sub:
        raise AuthError("LinkedIn userinfo response had no 'sub' claim.")
    return f"urn:li:person:{sub}"


def run_local_auth_flow(*, client_id: str, client_secret: str) -> str:
    """Run the 3-legged auth-code flow on localhost and return an access token.

    Opens the browser to LinkedIn's consent screen, captures the redirect on a
    short-lived local HTTP server, then exchanges the code for a token.
    """
    state = secrets.token_urlsafe(16)
    captured: dict[str, str] = {}
    done = threading.Event()

    class _Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            captured.update({k: v[0] for k, v in params.items()})
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"<h1>post-it: you can close this tab.</h1>")
            done.set()

        def log_message(self, *args):  # silence the default logging
            pass

    server = http.server.HTTPServer(("localhost", 8000), _Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    authorize = AUTH_URL + "?" + urllib.parse.urlencode(
        {
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": REDIRECT_URI,
            "state": state,
            "scope": SCOPES,
        }
    )
    webbrowser.open(authorize)
    print(f"If your browser didn't open, visit:\n{authorize}\n")

    done.wait(timeout=300)
    server.shutdown()

    if captured.get("state") != state:
        raise AuthError("OAuth state mismatch — aborting.")
    code = captured.get("code")
    if not code:
        raise AuthError(f"No authorization code returned: {captured}")

    try:
        token_resp = httpx.post(
            TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": REDIRECT_URI,
                "client_id": client_id,
                "client_secret": client_secret,
            },
            timeout=15.0,
        )
        token_resp.raise_for_status()
    except httpx.HTTPError as exc:
        raise AuthError(f"Token exchange failed: {exc}") from exc

    access_token = token_resp.json().get("access_token")
    if not access_token:
        raise AuthError("Token response had no access_token.")
    return access_token
