"""
youtube_auth.py — Web-based OAuth2 for multi-user Streamlit on Render
Uses state parameter to persist session across redirect
"""

import os
import json
import uuid
import streamlit as st
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request

SCOPES = [
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
]

# In-memory token store (per server instance)
# For production: replace with Redis or database
_TOKEN_STORE = {}

def get_client_config():
    env_secret = os.getenv("GOOGLE_CLIENT_SECRETS")
    if env_secret:
        return json.loads(env_secret)
    if os.path.exists("client_secret.json"):
        with open("client_secret.json") as f:
            return json.load(f)
    raise FileNotFoundError("No Google credentials found.")

def get_redirect_uri():
    render_url = os.getenv("RENDER_EXTERNAL_URL")
    if render_url:
        return f"{render_url}/oauth2callback"
    return "http://localhost:8501/oauth2callback"

def build_flow():
    config = get_client_config()
    flow = Flow.from_client_config(
        config,
        scopes=SCOPES,
        redirect_uri=get_redirect_uri()
    )
    return flow

def get_credentials():
    params = dict(st.query_params)

    # ── Step 1: Handle OAuth callback ──
    if "code" in params:
        try:
            flow = build_flow()
            flow.fetch_token(code=params["code"])
            creds = flow.credentials
            creds_json = json.loads(creds.to_json())

            # Generate session token and store credentials server-side
            session_token = str(uuid.uuid4())
            _TOKEN_STORE[session_token] = creds_json

            # Save session token to session_state AND redirect with token in URL
            st.session_state["session_token"] = session_token
            st.query_params.clear()
            st.query_params["session"] = session_token
            st.rerun()
        except Exception as e:
            st.error(f"Login failed: {e}")
            st.query_params.clear()
            return None

    # ── Step 2: Restore from URL session param ──
    if "session" in params:
        token = params["session"]
        st.session_state["session_token"] = token
        # Clean URL but keep session in state
        st.query_params.clear()
        st.rerun()

    # ── Step 3: Check session_state for stored token ──
    if "session_token" in st.session_state:
        token = st.session_state["session_token"]
        if token in _TOKEN_STORE:
            creds_json = _TOKEN_STORE[token]
            try:
                creds = Credentials.from_authorized_user_info(creds_json, SCOPES)
                if creds.valid:
                    return creds
                if creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                    _TOKEN_STORE[token] = json.loads(creds.to_json())
                    return creds
            except Exception:
                pass
        # Token expired or not found
        del st.session_state["session_token"]

    return None

def show_login_button():
    flow = build_flow()
    auth_url, _ = flow.authorization_url(
        prompt="consent",
        access_type="offline",
        include_granted_scopes="true"
    )
    return auth_url

def logout():
    if "session_token" in st.session_state:
        token = st.session_state["session_token"]
        if token in _TOKEN_STORE:
            del _TOKEN_STORE[token]
        del st.session_state["session_token"]